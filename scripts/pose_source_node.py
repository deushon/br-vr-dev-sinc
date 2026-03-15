#!/usr/bin/env python3
"""
Pose source: merges VR (/quest/poses) and Manual (/teleop_fetch/manual_poses).
Publishes to /teleop_fetch/poses for fast_ik.
Mode: /teleop_fetch/pose_mode (std_msgs/String) "vr" | "manual"
"""

import rospy
from geometry_msgs.msg import PoseArray
from std_msgs.msg import String


class PoseSourceNode:
    def __init__(self):
        rospy.init_node('pose_source', anonymous=False)
        self.mode = 'vr'
        self.quest_poses = None
        self.manual_poses = None

        self.pub = rospy.Publisher('/teleop_fetch/poses', PoseArray, queue_size=1)
        rospy.Subscriber('/quest/poses', PoseArray, self._quest_cb)
        rospy.Subscriber('/teleop_fetch/manual_poses', PoseArray, self._manual_cb)
        rospy.Subscriber('/teleop_fetch/pose_mode', String, self._mode_cb)

        self.timer = rospy.Timer(rospy.Duration(0.02), self._publish)  # 50 Hz
        rospy.loginfo('pose_source: VR + Manual merge -> /teleop_fetch/poses')

    def _quest_cb(self, msg):
        self.quest_poses = msg

    def _manual_cb(self, msg):
        self.manual_poses = msg

    def _mode_cb(self, msg):
        self.mode = msg.data if msg.data in ('vr', 'manual') else self.mode

    def _publish(self, event):
        if self.mode == 'manual' and self.manual_poses and len(self.manual_poses.poses) >= 3:
            self.pub.publish(self.manual_poses)
        elif self.quest_poses and len(self.quest_poses.poses) >= 3:
            self.pub.publish(self.quest_poses)


def main():
    try:
        node = PoseSourceNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
