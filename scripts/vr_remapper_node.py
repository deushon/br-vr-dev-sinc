#!/usr/bin/env python3
"""
VR Remapper: единственное место преобразования данных контроллеров.

Подписывается на /quest/poses, применяет ТОЛЬКО функцию _controller_to_body_link
к позициям левой и правой руки. Голова передаётся без изменений.

Публикует в /teleop_fetch/quest_poses_remapped.
"""

import copy
import rospy
from geometry_msgs.msg import PoseArray


def _controller_to_body_link(x, y, z, is_left):
    """
    ЕДИНСТВЕННОЕ МЕСТО: поменять местами значения и знаки для каждого контроллера.

    Вход: x, y, z — сырые координаты с Quest (position.x, .y, .z)
    Выход: (x_out, y_out, z_out) для body_link (X вперёд, Y влево, Z вверх)

    Примеры:
      swap Y и Z:     return (x, z, y)
      инвертировать Y: return (x, -y, z)
      swap + инверт:  return (x, -z, -y)
    """
    if is_left:
        # Левый контроллер
        return (z, -x, y)
    else:
        # Правый контроллер
        return (z, -x, y)


class VRRemapperNode:
    def __init__(self):
        rospy.init_node('vr_remapper', anonymous=False)
        self.quest_poses = None
        self.pub = rospy.Publisher('/teleop_fetch/quest_poses_remapped', PoseArray, queue_size=1)
        rospy.Subscriber('/quest/poses', PoseArray, self._quest_cb)
        rospy.loginfo('vr_remapper: Quest -> body_link (только _controller_to_body_link)')

    def _quest_cb(self, msg):
        self.quest_poses = msg

    def _publish(self, event):
        if not self.quest_poses or len(self.quest_poses.poses) < 3:
            return
        out = copy.deepcopy(self.quest_poses)

        p = self.quest_poses.poses[1].position
        x, y, z = _controller_to_body_link(p.x, p.y, p.z, is_left=True)
        out.poses[1].position.x, out.poses[1].position.y, out.poses[1].position.z = x, y, z

        p = self.quest_poses.poses[2].position
        x, y, z = _controller_to_body_link(p.x, p.y, p.z, is_left=False)
        out.poses[2].position.x, out.poses[2].position.y, out.poses[2].position.z = x, y, z

        self.pub.publish(out)

    def run(self):
        rospy.Timer(rospy.Duration(0.02), self._publish)
        rospy.spin()


def main():
    try:
        node = VRRemapperNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
