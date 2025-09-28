#!/usr/bin/env python3

import rospy
import numpy as np
from geometry_msgs.msg import PoseArray
from sensor_msgs.msg import JointState
from teleop_fetch.msg import HeadCommand
from ros_robot_controller.msg import SetBusServosPosition, BusServoPosition


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
        
        # Публикатор для управления руками робота
        self.arms_pub = rospy.Publisher('/ros_robot_controller/bus_servo/set_position', SetBusServosPosition, queue_size=1)
        
        # Подписчики на данные от VR гарнитуры
        rospy.Subscriber('/quest/poses', PoseArray, self.pose_callback, queue_size=10)
        rospy.Subscriber('/quest/joints', JointState, self.joints_callback, queue_size=10)
        
        # Текущие позиции головы робота
        self.current_head_pan = 0.0
        self.current_head_tilt = 0.0
        
        # Данные о положении головы оператора
        self.operator_head_pose = None
        self.operator_head_orientation = None
        
        # Данные о состоянии VR контроллеров
        self.vr_controllers_state = {
            'left_grip': 0.0,
            'left_index': 0.0,
            'left_x': 0.0,
            'left_y': 0.0,
            'right_grip': 0.0,
            'right_index': 0.0,
            'right_a': 0.0,
            'right_b': 0.0
        }
        
        # Стартовые позиции для рук робота
        self.arm_start_positions = {
            # Правая рука
            14: 126,   # Правое плечо, вперед-назад
            16: 167,   # Правое плечо вверх-вниз
            18: 498,   # Правое предплечье поворот
            20: 956,   # Правое предплечье сгибание локтя
            22: 500,   # Правый захват руки (сжимает/разжимает руку)
            
            # Левая рука
            13: 874,   # Левое плечо вперед-назад
            15: 833,   # Левое плечо вверх-вниз
            17: 502,   # Левое предплечье поворот
            19: 44,    # Левое предплечье сгибание локтя
            21: 500    # Левый захват руки (сжимает/разжимает руку)
        }
        
        rospy.loginfo("TeleopFetcher нода инициализирована")
        rospy.loginfo(f"Чувствительность головы: {self.head_sensitivity}")
        rospy.loginfo(f"Максимальный поворот головы: ±{self.max_head_pan}")
        rospy.loginfo(f"Максимальный наклон головы: ±{self.max_head_tilt}")
        rospy.loginfo("Подписка на топики:")
        rospy.loginfo("  - /quest/poses: данные о положении головы и рук оператора")
        rospy.loginfo("  - /quest/joints: данные о кнопках и джойстиках VR контроллеров")
        rospy.loginfo("Готов к получению данных от VR гарнитуры Quest")
        
        # Устанавливаем начальную позу рук
        self.set_arms_to_start_position()
    
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
        Обрабатывает данные о кнопках и джойстиках VR контроллеров.
        
        Ожидаемые данные:
        - L_grip, L_index: левый контроллер (хватка и триггер)
        - R_grip, R_index: правый контроллер (хватка и триггер)  
        - L_X, L_Y: левые кнопки (X и Y кнопки)
        - R_A, R_B: правые кнопки (A и B кнопки)
        """
        if joint_state.name and joint_state.position:
            joint_dict = dict(zip(joint_state.name, joint_state.position))
            
            # Извлекаем данные о контроллерах
            left_grip = joint_dict.get('L_grip', 0.0)
            left_index = joint_dict.get('L_index', 0.0)
            right_grip = joint_dict.get('R_grip', 0.0)
            right_index = joint_dict.get('R_index', 0.0)
            
            # Извлекаем данные о кнопках
            left_x = joint_dict.get('L_X', 0.0)
            left_y = joint_dict.get('L_Y', 0.0)
            right_a = joint_dict.get('R_A', 0.0)
            right_b = joint_dict.get('R_B', 0.0)
            
            # Логируем полученные данные (с ограничением частоты)
            rospy.loginfo_throttle(2, 
                f"VR контроллеры - Левый: grip={left_grip:.2f}, index={left_index:.2f}, "
                f"кнопки X={left_x:.2f}, Y={left_y:.2f} | "
                f"Правый: grip={right_grip:.2f}, index={right_index:.2f}, "
                f"кнопки A={right_a:.2f}, B={right_b:.2f}"
            )
            
            # TODO: Добавить обработку команд для управления руками робота
            # Здесь можно будет использовать данные о кнопках контроллеров
            # для управления захватом, движением рук и т.д.
            self.process_vr_controller_input(
                left_grip, left_index, left_x, left_y,
                right_grip, right_index, right_a, right_b
            )
    
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
        
        # Применяем чувствительность и ограничения с инверсией
        # Инвертируем управление: оператор поворачивает влево -> робот поворачивается вправо
        target_pan = np.clip(-y_rotation * self.head_sensitivity, -self.max_head_pan, self.max_head_pan)
        target_tilt = np.clip(-x_rotation * self.head_sensitivity, -self.max_head_tilt, self.max_head_tilt)
        
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
    
    def process_vr_controller_input(self, left_grip, left_index, left_x, left_y, 
                                   right_grip, right_index, right_a, right_b):
        """
        Обработка входных данных от VR контроллеров.
        
        Args:
            left_grip, left_index: левый контроллер (хватка и триггер)
            left_x, left_y: левые кнопки (X и Y кнопки)
            right_grip, right_index: правый контроллер (хватка и триггер)
            right_a, right_b: правые кнопки (A и B кнопки)
        """
        # Сохраняем текущее состояние контроллеров
        self.vr_controllers_state.update({
            'left_grip': left_grip,
            'left_index': left_index,
            'left_x': left_x,
            'left_y': left_y,
            'right_grip': right_grip,
            'right_index': right_index,
            'right_a': right_a,
            'right_b': right_b
        })
        
        # TODO: Реализовать обработку команд от VR контроллеров
        # Примеры возможного использования:
        
        # 1. Управление захватом рук робота
        # if left_grip > 0.5:  # Хватка левой руки
        #     self.control_left_gripper(left_grip)
        # if right_grip > 0.5:  # Хватка правой руки
        #     self.control_right_gripper(right_grip)
        
        # 2. Управление функциональными кнопками
        # if left_x > 0.5:  # Кнопка X - функция левой руки
        #     self.execute_left_hand_function_x()
        # if left_y > 0.5:  # Кнопка Y - функция левой руки
        #     self.execute_left_hand_function_y()
        
        # 3. Функциональные кнопки правого контроллера
        # if right_a > 0.5:  # Кнопка A - какая-то функция
        #     self.execute_function_a()
        # if right_b > 0.5:  # Кнопка B - другая функция
        #     self.execute_function_b()
        
        # 4. Триггеры для точных действий
        # if left_index > 0.5:  # Левый триггер
        #     self.execute_precise_action_left()
        # if right_index > 0.5:  # Правый триггер
        #     self.execute_precise_action_right()
        
        pass
    
    def process_arms_control(self, left_hand_pose, right_hand_pose):
        """
        Обработка управления руками робота на основе положения рук оператора.
        Пока не реализовано, но структура готова для будущего расширения.
        """
        # TODO: Реализовать управление руками
        # Здесь будет логика преобразования положения рук оператора
        # в команды управления руками робота
        pass
    
    def set_arms_to_start_position(self):
        """
        Устанавливает руки робота в стартовую позицию.
        Отправляет команды на все сервоприводы рук с заданными позициями.
        """
        rospy.loginfo("Установка рук робота в стартовую позицию...")
        
        # Создаем сообщение для установки позиций сервоприводов
        arm_msg = SetBusServosPosition()
        arm_msg.duration = 0.1  # Время на перемещение в секундах
        
        # Создаем список позиций для всех сервоприводов рук
        positions = []
        for servo_id, position in self.arm_start_positions.items():
            servo_pos = BusServoPosition()
            servo_pos.id = servo_id
            servo_pos.position = position
            positions.append(servo_pos)
            
            rospy.loginfo(f"Сервопривод ID{servo_id}: позиция {position}")
        
        arm_msg.position = positions
        
        # Отправляем команду
        self.arms_pub.publish(arm_msg)
        rospy.loginfo("Команда установки стартовой позы рук отправлена")
        rospy.loginfo(f"Установлено {len(positions)} сервоприводов")
        
        # Ждем завершения движения
        rospy.sleep(arm_msg.duration + 0.5)  # Небольшая задержка для завершения
        rospy.loginfo("Стартовая поза рук установлена")
    
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
