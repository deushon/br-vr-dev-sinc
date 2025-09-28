#!/usr/bin/env python3

import rospy
from teleop_fetch.msg import HeadCommand

def test_head_command():
    """
    Тестовый скрипт для проверки структуры сообщения HeadCommand.
    """
    rospy.init_node('test_head_command', anonymous=True)
    
    # Создаем публикатор
    pub = rospy.Publisher('/test_head_command', HeadCommand, queue_size=1)
    
    # Создаем тестовое сообщение
    msg = HeadCommand()
    msg.position = 0.5
    msg.duration = 0.2
    
    rospy.loginfo(f"Тестовое сообщение: position={msg.position}, duration={msg.duration}")
    
    # Публикуем сообщение
    pub.publish(msg)
    rospy.loginfo("Сообщение опубликовано")
    
    rospy.sleep(1)

if __name__ == '__main__':
    try:
        test_head_command()
    except rospy.ROSInterruptException:
        pass
