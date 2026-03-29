#!/usr/bin/env python3
"""
teleop_fetch - unified VR teleoperation node.
Single point of publication to bus_servo.
"""

import rospy
from geometry_msgs.msg import PoseArray
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from ainex_interfaces.msg import HeadState
from ros_robot_controller.msg import SetBusServosPosition

# Dynamic imports to handle potential missing message types before they are built
try:
    from teleop_fetch.srv import ReceiveGrant, ReceiveGrantResponse, EndSession, EndSessionResponse
except ImportError:
    pass
try:
    from KYR.srv import OpenSession, CloseSession
except ImportError:
    pass

from teleop_fetch.config import load_config
from teleop_fetch.vr_adapter import (
    VRData,
    pose_array_to_vr_data,
    joint_state_to_dict,
    update_vr_data_from_joints,
)
from teleop_fetch.head_controller import (
    compute_head_targets,
    create_head_state_msg,
)
from teleop_fetch.start_stop_controller import (
    build_arm_start_positions_msg,
    build_reset_grippers_msg,
)
from teleop_fetch.operator_buttons import rising_edge

# Quest left controller: L_X = start streaming, L_Y = stop (joints on ~vr_input/joints_topic)
_BUTTON_THRESH = 0.5


class TeleopNode:
    def __init__(self):
        rospy.init_node('teleop_fetch', anonymous=False)
        self.config = load_config()

        # State machine: IDLE, REQUESTED, PENDING_GRANT, ACTIVE, FINISHED, FAILED
        self.session_state = 'IDLE'

        # VR data cache
        self.vr_data = VRData()

        # After KYR ACTIVE: wait for L_X before forwarding arms / head; L_Y disarms (session stays ACTIVE).
        self.operator_armed = False
        self._prev_lx = 0.0
        self._prev_ly = 0.0
        self._xy_edges_need_sync = True

        # Publishers - now point to KYR proxy topics to ensure authorization
        self.servo_pub = rospy.Publisher(
            "/kyr/bus_servo_in",
            SetBusServosPosition,
            queue_size=1,
        )
        self.head_pan_pub = rospy.Publisher(
            self.config['head']['pan_topic'],
            HeadState,
            queue_size=1,
        )
        self.head_tilt_pub = rospy.Publisher(
            self.config['head']['tilt_topic'],
            HeadState,
            queue_size=1,
        )
        # Latched so operators (rosbridge / late subscribers) still see get_control after connect.
        self.teleop_state_pub = rospy.Publisher(
            self.config['teleop_state_topic'],
            String,
            queue_size=1,
            latch=True,
        )

        # Subscribers
        rospy.Subscriber(
            self.config['poses_topic'],
            PoseArray,
            self._pose_callback,
            queue_size=10,
        )
        rospy.Subscriber(
            self.config['joints_topic'],
            JointState,
            self._joints_callback,
            queue_size=10,
        )
        rospy.Subscriber(
            self.config['arm_servo_targets_topic'],
            SetBusServosPosition,
            self._arm_targets_callback,
            queue_size=10,
        )

        # Services for lifecycle
        try:
            rospy.Service('~receive_grant', ReceiveGrant, self._handle_receive_grant)
            rospy.Service('~end_session', EndSession, self._handle_end_session)
        except NameError:
            rospy.logwarn("teleop_fetch services not available. Run catkin_make and source first.")

        # KYR Clients
        self.kyr_open_session = rospy.ServiceProxy('/kyr/open_session', OpenSession)
        self.kyr_close_session = rospy.ServiceProxy('/kyr/close_session', CloseSession)

        rospy.loginfo('teleop_fetch initialized, session_state=IDLE.')

    def _handle_receive_grant(self, req):
        if self.session_state in ['ACTIVE', 'PENDING_GRANT']:
            return ReceiveGrantResponse(success=False, message="Session already active or pending")
        
        self.session_state = 'PENDING_GRANT'
        rospy.loginfo("Received grant, opening session in KYR...")
        
        try:
            rospy.wait_for_service('/kyr/open_session', timeout=2.0)
            res = self.kyr_open_session(req.grant_payload, req.signature)
            if res.success:
                self.session_state = 'ACTIVE'
                self.current_session_id = res.session_id
                rospy.loginfo(f"KYR session {res.session_id} opened. State -> ACTIVE")
                self.operator_armed = False
                self._xy_edges_need_sync = True
                self._publish_arm_start_position()
                rospy.loginfo(
                    'Session ACTIVE: press L_X (Quest) to arm teleop; L_Y to disarm. /teleop_state: get_control on X.'
                )
                return ReceiveGrantResponse(success=True, message=res.message)
            else:
                self.session_state = 'FAILED'
                rospy.logwarn(f"KYR denied session: {res.message}. State -> FAILED")
                return ReceiveGrantResponse(success=False, message=res.message)
        except rospy.ServiceException as e:
            self.session_state = 'FAILED'
            msg = f"Failed to call KYR open_session: {e}"
            rospy.logerr(msg)
            return ReceiveGrantResponse(success=False, message=msg)

    def _handle_end_session(self, req):
        if self.session_state != 'ACTIVE':
            return EndSessionResponse(success=False, message="No active session to end")
            
        self._stop_arm_control()
        
        try:
            rospy.wait_for_service('/kyr/close_session', timeout=2.0)
            res = self.kyr_close_session(self.current_session_id, req.reason)
            # The receipt processing and post-pay happens in rospy_x402, not here.
            # Here we just notify KYR.
            return EndSessionResponse(success=res.success, message=res.message)
        except rospy.ServiceException as e:
            msg = f"Failed to call KYR close_session: {e}"
            rospy.logerr(msg)
            return EndSessionResponse(success=False, message=msg)

    def _pose_callback(self, msg):
        data = pose_array_to_vr_data(msg)
        self.vr_data.head_pose = data.head_pose
        self.vr_data.head_orientation = data.head_orientation
        self.vr_data.left_hand_pose = data.left_hand_pose
        self.vr_data.right_hand_pose = data.right_hand_pose

        if self.session_state == 'ACTIVE' and self.operator_armed:
            self._process_head_control()

    def _joints_callback(self, msg):
        joint_dict = joint_state_to_dict(msg)
        update_vr_data_from_joints(self.vr_data, joint_dict)
        self._process_operator_xy_buttons()

    def _process_operator_xy_buttons(self):
        if self.session_state != 'ACTIVE':
            return
        lx = self.vr_data.left_x
        ly = self.vr_data.left_y
        if self._xy_edges_need_sync:
            self._prev_lx = lx
            self._prev_ly = ly
            self._xy_edges_need_sync = False
            return
        y_edge = rising_edge(self._prev_ly, ly, _BUTTON_THRESH)
        x_edge = rising_edge(self._prev_lx, lx, _BUTTON_THRESH)
        self._prev_lx = lx
        self._prev_ly = ly
        if y_edge and self.operator_armed:
            self._operator_y_disarm()
        elif x_edge and not self.operator_armed:
            self.operator_armed = True
            self._publish_teleop_state('get_control')
            rospy.loginfo('L_X: operator armed — streaming arms/head to robot')

    def _process_head_control(self):
        pan, tilt = compute_head_targets(
            self.vr_data.head_orientation,
            self.config['head'],
        )
        if pan is not None and tilt is not None:
            duration = self.config['head']['movement_duration']
            pan_msg = create_head_state_msg(pan, duration)
            tilt_msg = create_head_state_msg(tilt, duration)
            self.head_pan_pub.publish(pan_msg)
            self.head_tilt_pub.publish(tilt_msg)

    def _stop_arm_control(self):
        self.operator_armed = False
        self._xy_edges_need_sync = True
        self._publish_teleop_state('stop_control')
        self.session_state = 'FINISHED'
        rospy.loginfo('Arm control DISABLED, session FINISHED')
        self._publish_arm_start_position()
        self._reset_head_to_base()
        self._reset_grippers()

    def _operator_y_disarm(self):
        """L_Y: stop streaming; KYR session remains ACTIVE (press L_X again to resume)."""
        self.operator_armed = False
        self._xy_edges_need_sync = True
        self._publish_teleop_state('stop_control')
        self._publish_arm_start_position()
        self._reset_head_to_base()
        self._reset_grippers()
        rospy.loginfo('L_Y: operator disarmed (session still ACTIVE)')

    def _publish_teleop_state(self, data):
        """Operator feedback: L_X→get_control, L_Y or end_session→stop_control."""
        self.teleop_state_pub.publish(String(data=data))
        rospy.loginfo('Published /teleop_state: %s', data)

    def _publish_arm_start_position(self):
        msg = build_arm_start_positions_msg(self.config, duration=0.1)
        self.servo_pub.publish(msg)
        rospy.loginfo('Published arm start positions')

    def _reset_head_to_base(self):
        pan_msg = create_head_state_msg(0.0, self.config['head']['movement_duration'])
        tilt_msg = create_head_state_msg(0.0, self.config['head']['movement_duration'])
        self.head_pan_pub.publish(pan_msg)
        self.head_tilt_pub.publish(tilt_msg)
        rospy.loginfo('Head reset to base')

    def _reset_grippers(self):
        msg = build_reset_grippers_msg(self.config)
        self.servo_pub.publish(msg)
        rospy.loginfo('Grippers reset')

    def _arm_targets_callback(self, msg):
        """Forward arm targets from fast_ik to KYR proxy when session armed (L_X)."""
        if self.session_state != 'ACTIVE' or not self.operator_armed:
            return
        self.servo_pub.publish(msg)

    def run(self):
        rospy.spin()


def main():
    try:
        node = TeleopNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo('teleop_fetch stopped')


if __name__ == '__main__':
    main()
