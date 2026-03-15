#!/usr/bin/env python3
"""
VR Remapper: ремаппинг ТОЛЬКО данных контроллеров Quest → body_link.

Подписывается на /quest/poses, применяет axis_mapping и post_mapping
только к позициям левой и правой руки (poses[1], poses[2]).
Голова (poses[0]) передаётся без изменений.

Публикует в /teleop_fetch/quest_poses_remapped.
Manual mode не затрагивается — pose_source использует manual_poses напрямую.
"""

import rospy
from geometry_msgs.msg import PoseArray
from std_msgs.msg import String, Float64MultiArray


def _apply_axis_mapping(x, y, z, mapping):
    """Quest frame → промежуточный body_link (как в fast_ik rotate_pose_in_axis)."""
    if mapping == "xz":
        return (-z, y, -x)
    if mapping == "yz":
        return (x, -z, -y)
    if mapping == "swap_yz":
        return (x, z, y)
    if mapping == "swap_xz":
        return (z, y, x)
    if mapping == "none":
        return (x, y, z)
    if mapping == "inv_y":
        return (x, -y, z)
    if mapping == "inv_z":
        return (x, y, -z)
    if mapping == "inv_yz":
        return (x, -y, -z)
    # "xy" default
    return (-y, -x, z)


def _apply_post_mapping(x, y, z, swap_yz, inv_y, inv_z, swap_right_only, is_right):
    """Swap Y↔Z и инверсии — только для контроллеров."""
    do_swap = swap_yz and (not swap_right_only or is_right)
    if do_swap:
        y, z = z, y
    if inv_y:
        y = -y
    if inv_z:
        z = -z
    return x, y, z


class VRRemapperNode:
    def __init__(self):
        rospy.init_node('vr_remapper', anonymous=False)
        self.quest_poses = None
        self.axis_mapping = rospy.get_param('~axis_mapping', 'xy')
        self.swap_yz = False
        self.inv_y = False
        self.inv_z = False
        self.swap_right_only = False

        self.pub = rospy.Publisher('/teleop_fetch/quest_poses_remapped', PoseArray, queue_size=1)
        rospy.Subscriber('/quest/poses', PoseArray, self._quest_cb)
        rospy.Subscriber('/teleop_fetch/axis_mapping', String, self._axis_cb)
        rospy.Subscriber('/teleop_fetch/post_mapping', Float64MultiArray, self._post_cb)

        rospy.loginfo('vr_remapper: Quest controllers -> body_link (axis mapping + post_mapping)')

    def _quest_cb(self, msg):
        self.quest_poses = msg

    def _axis_cb(self, msg):
        self.axis_mapping = msg.data

    def _post_cb(self, msg):
        if len(msg.data) >= 3:
            self.swap_yz = msg.data[0] != 0
            self.inv_y = msg.data[1] != 0
            self.inv_z = msg.data[2] != 0
            self.swap_right_only = len(msg.data) >= 4 and msg.data[3] != 0

    def _publish(self, event):
        if not self.quest_poses or len(self.quest_poses.poses) < 3:
            return
        out = PoseArray()
        out.header = self.quest_poses.header
        out.poses = list(self.quest_poses.poses)  # copy

        # Head — без изменений
        # out.poses[0] = self.quest_poses.poses[0].position unchanged

        # Left hand (index 1)
        p = self.quest_poses.poses[1].position
        x, y, z = _apply_axis_mapping(p.x, p.y, p.z, self.axis_mapping)
        x, y, z = _apply_post_mapping(x, y, z, self.swap_yz, self.inv_y, self.inv_z,
                                      self.swap_right_only, is_right=False)
        out.poses[1].position.x = x
        out.poses[1].position.y = y
        out.poses[1].position.z = z

        # Right hand (index 2)
        p = self.quest_poses.poses[2].position
        x, y, z = _apply_axis_mapping(p.x, p.y, p.z, self.axis_mapping)
        x, y, z = _apply_post_mapping(x, y, z, self.swap_yz, self.inv_y, self.inv_z,
                                      self.swap_right_only, is_right=True)
        out.poses[2].position.x = x
        out.poses[2].position.y = y
        out.poses[2].position.z = z

        self.pub.publish(out)

    def run(self):
        rospy.Timer(rospy.Duration(0.02), self._publish)  # 50 Hz
        rospy.spin()


def main():
    try:
        node = VRRemapperNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
