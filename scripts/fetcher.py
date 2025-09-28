#!/usr/bin/env python3

import rospy
import numpy as np
from geometry_msgs.msg import PoseArray
from sensor_msgs.msg import JointState
from teleop_fetch.msg import HeadCommand


class TeleopFetcher:
    """
    ROS нода для телеоперации робота Fetch на основе данных от VR гарнитуры.
    Управляет головой робота на основе положения головы оператора.
    Структура готова для добавления контроля рук в будущем.
    """
    
    def __init__(self):
        rospy.init_node('teleop_fetch', anonymous=True)
        
        # Параметры для настройки чувствительности
        self.head_sensitivity = rospy.get_param('~head_sensitivity', 1.0)
        self.max_head_pan = rospy.get_param('~max_head_pan', 2.0)  # Максимальный поворот головы
        self.max_head_tilt = rospy.get_param('~max_head_tilt', 2.0)  # Максимальный наклон головы
        self.movement_duration = rospy.get_param('~movement_duration', 0.2)  # Время на перемещение
        
        # Публикаторы для управления головой
        self.head_pan_pub = rospy.Publisher('/head_pan_controller/command', HeadCommand, queue_size=1)
        self.head_tilt_pub = rospy.Publisher('/head_tilt_controller/command', HeadCommand, queue_size=1)
        
        # Подписчики на данные от VR гарнитуры
        rospy.Subscriber('/quest/poses', PoseArray, self.pose_callback, queue_size=10)
        rospy.Subscriber('/quest/joints', JointState, self.joints_callback, queue_size=10)
        
        # Текущие позиции головы робота
        self.current_head_pan = 0.0
        self.current_head_tilt = 0.0
        
        # Данные о положении головы оператора
        self.operator_head_pose = None
        self.operator_head_orientation = None
        
        rospy.loginfo("TeleopFetcher нода инициализирована")
        rospy.loginfo(f"Чувствительность головы: {self.head_sensitivity}")
        rospy.loginfo(f"Максимальный поворот головы: ±{self.max_head_pan}")
        rospy.loginfo(f"Максимальный наклон головы: ±{self.max_head_tilt}")
    
    def pose_callback(self, pose_array):
        """
        Обработка данных о положении головы и рук оператора.
        poses[0] = head (abs, frame_id: "unity_world")
        poses[1] = left hand (relative-to-head)
        poses[2] = right hand (relative-to-head)
        """
        if len(pose_array.poses) < 3:
            rospy.logwarn("Получен неполный PoseArray")
            return
        
        # Извлекаем данные о голове оператора
        head_pose = pose_array.poses[0]
        self.operator_head_pose = head_pose.position
        self.operator_head_orientation = head_pose.orientation
        
        # Обрабатываем управление головой
        self.process_head_control()
        
        # TODO: Добавить обработку рук в будущем
        # left_hand_pose = pose_array.poses[1]
        # right_hand_pose = pose_array.poses[2]
        # self.process_arms_control(left_hand_pose, right_hand_pose)
    
    def joints_callback(self, joint_state):
        """
        Обработка данных о суставах рук оператора.
        Пока не используется, но готова для будущего расширения.
        """
        if joint_state.name and joint_state.position:
            joint_dict = dict(zip(joint_state.name, joint_state.position))
            # TODO: Обработка данных о суставах рук
            # rospy.loginfo_throttle(1, f"Получены данные о суставах: {len(joint_dict)} суставов")
            pass
    
    def process_head_control(self):
        """
        Обработка управления головой на основе положения головы оператора.
        Преобразует ориентацию головы оператора в команды управления головой робота.
        """
        if self.operator_head_orientation is None:
            return
        
        # Извлекаем углы Эйлера из кватерниона
        # Y отвечает за повороты головы влево-вправо (-1 до 1)
        # X отвечает за наклоны головы вверх-вниз (-1 до 1)
        euler_angles = self.quaternion_to_euler(
            self.operator_head_orientation.x,
            self.operator_head_orientation.y,
            self.operator_head_orientation.z,
            self.operator_head_orientation.w
        )
        
        # Преобразуем углы в команды управления
        # Y -> pan (поворот влево-вправо)
        # X -> tilt (наклон вверх-вниз)
        y_rotation = euler_angles[1]  # Yaw (поворот вокруг Z)
        x_rotation = euler_angles[0]  # Pitch (наклон вокруг Y)
        
        # Применяем чувствительность и ограничения
        target_pan = np.clip(y_rotation * self.head_sensitivity, -self.max_head_pan, self.max_head_pan)
        target_tilt = np.clip(x_rotation * self.head_sensitivity, -self.max_head_tilt, self.max_head_tilt)
        
        # Отправляем команды управления головой
        self.send_head_command(target_pan, target_tilt)
    
    def quaternion_to_euler(self, x, y, z, w):
        """
        Преобразование кватерниона в углы Эйлера (roll, pitch, yaw).
        """
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = np.copysign(np.pi / 2, sinp)  # use 90 degrees if out of range
        else:
            pitch = np.arcsin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return [roll, pitch, yaw]
    
    def send_head_command(self, pan, tilt):
        """
        Отправка команд управления головой робота.
        Структура сообщения: HeadCommand(position, duration)
        """
        # Создаем сообщения для управления головой
        pan_msg = HeadCommand()
        pan_msg.position = pan
        pan_msg.duration = self.movement_duration
        
        tilt_msg = HeadCommand()
        tilt_msg.position = tilt
        tilt_msg.duration = self.movement_duration
        
        # Публикуем команды
        self.head_pan_pub.publish(pan_msg)
        self.head_tilt_pub.publish(tilt_msg)
        
        # Обновляем текущие позиции
        self.current_head_pan = pan
        self.current_head_tilt = tilt
        
        # Логируем команды (с ограничением частоты)
        rospy.loginfo_throttle(0.5, f"Команды головы - Pan: {pan:.3f}, Tilt: {tilt:.3f}, Duration: {self.movement_duration}")
    
    def process_arms_control(self, left_hand_pose, right_hand_pose):
        """
        Обработка управления руками робота.
        Пока не реализовано, но структура готова для будущего расширения.
        """
        # TODO: Реализовать управление руками
        # Здесь будет логика преобразования положения рук оператора
        # в команды управления руками робота
        pass
    
    def run(self):
        """
        Основной цикл работы ноды.
        """
        rospy.loginfo("TeleopFetcher нода запущена")
        rospy.spin()


if __name__ == '__main__':
    try:
        teleop_fetcher = TeleopFetcher()
        teleop_fetcher.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("TeleopFetcher нода остановлена")
