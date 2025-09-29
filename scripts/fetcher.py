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
    Управляет головой и руками робота на основе положения головы и контроллеров оператора.
    
    Новая система управления руками:
    - Y контроллера -> sho_pitch (плечо вперед-назад)
    - Z контроллера -> sho_roll (плечо вверх-вниз)
    - X контроллера -> el_yaw (предплечье поворот)
    - Наклон X контроллера -> el_pitch (предплечье сгибание)
    
    Калибровка выполняется отдельно для каждой руки.
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
        
        # Базовые позиции головы для сброса
        self.head_base_pan = 0.0
        self.head_base_tilt = 0.0
        
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
        
        # Данные о ориентации контроллеров (для получения наклона)
        self.left_controller_orientation = None
        self.right_controller_orientation = None
        
        # Состояния управления руками и головой
        self.arm_control_state = 'idle'  # 'idle', 'calibrating', 'controlling'
        self.head_control_enabled = False  # Управление головой включено/выключено
        
        # Состояния захватов (для запоминания последнего положения)
        # Центральное положение = 500, пределы ±200
        self.left_gripper_state = 0.5   # 0.0 = закрыт, 1.0 = открыт (инвертировано)
        self.right_gripper_state = 0.5   # 0.0 = закрыт, 1.0 = открыт
        # Система калибровки для каждой руки отдельно
        self.calibration_data = {
            'left_hand_base': None,   # Базовое положение левой руки при калибровке
            'right_hand_base': None,  # Базовое положение правой руки при калибровке
            'left_controller_base': None,  # Базовое положение левого контроллера
            'right_controller_base': None,  # Базовое положение правого контроллера
            'head_base': None         # Базовое положение головы при калибровке
        }
        
        # Калибровочные значения для каждой руки
        self.left_arm_calibration = {
            'sho_pitch_base': 874,    # l_sho_pitch базовая позиция
            'sho_roll_base': 833,     # l_sho_roll базовая позиция  
            'el_yaw_base': 44,        # l_el_yaw базовая позиция
            'el_pitch_base': 502      # l_el_pitch базовая позиция
        }
        
        self.right_arm_calibration = {
            'sho_pitch_base': 126,    # r_sho_pitch базовая позиция
            'sho_roll_base': 167,     # r_sho_roll базовая позиция
            'el_yaw_base': 956,       # r_el_yaw базовая позиция
            'el_pitch_base': 498      # r_el_pitch базовая позиция
        }
        
        # Отслеживание нажатий кнопок для предотвращения повторных срабатываний
        self.button_states = {
            'left_x_pressed': False,
            'left_y_pressed': False
        }
        
        # Масштабирование (робот в 5 раз меньше оператора)
        self.scale_factor = 0.2  # 1/5 = 0.2
        
        # Коэффициенты чувствительности для новой системы управления
        # Y -> sho_pitch, Z -> sho_roll, X -> el_yaw, наклон X -> el_pitch
        self.arm_sensitivity = {
            'y_to_sho_pitch': 70,      # Y контроллера -> sho_pitch
            'z_to_sho_roll': 70,       # Z контроллера -> sho_roll  
            'x_to_el_yaw': 70,         # X контроллера -> el_yaw
            'tilt_x_to_el_pitch': 35   # Наклон X контроллера -> el_pitch
        }
        
        # Стартовые позиции для рук робота (оригинальные значения с правильными ID)
        self.arm_start_positions = {
            # Правая рука (правильные ID из URDF)
            14: 126,   # r_sho_pitch - правое плечо вперед-назад
            16: 167,   # r_sho_roll - правое плечо вверх-вниз
            18: 498,   # r_el_pitch - правое предплечье поворот
            20: 956,   # r_el_yaw - правое предплечье сгибание
            22: 500,   # r_gripper - правый захват
            
            # Левая рука (правильные ID из URDF)
            13: 874,   # l_sho_pitch - левое плечо вперед-назад
            15: 833,   # l_sho_roll - левое плечо вверх-вниз
            17: 502,   # l_el_pitch - левое предплечье поворот
            19: 44,    # l_el_yaw - левое предплечье сгибание
            21: 500    # l_gripper - левый захват
        }
        
        rospy.loginfo("TeleopFetcher нода инициализирована")
        rospy.loginfo(f"Чувствительность головы: {self.head_sensitivity}")
        rospy.loginfo(f"Максимальный поворот головы: ±{self.max_head_pan}")
        rospy.loginfo(f"Максимальный наклон головы: ±{self.max_head_tilt}")
        rospy.loginfo("Подписка на топики:")
        rospy.loginfo("  - /quest/poses: данные о положении головы и рук оператора")
        rospy.loginfo("  - /quest/joints: данные о кнопках и джойстиках VR контроллеров")
        rospy.loginfo("Готов к получению данных от VR гарнитуры Quest")
        rospy.loginfo(f"Начальное состояние управления руками: {self.arm_control_state}")
        rospy.loginfo(f"Управление головой: {'включено' if self.head_control_enabled else 'отключено'}")
        rospy.loginfo("Для калибровки нажмите X на левом контроллере")
        
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
        
        # Обрабатываем управление руками
        left_hand_pose = pose_array.poses[1]
        right_hand_pose = pose_array.poses[2]
        
        # Сохраняем ориентацию контроллеров для получения наклона
        self.left_controller_orientation = left_hand_pose.orientation
        self.right_controller_orientation = right_hand_pose.orientation
        
        # Сохраняем последние данные о руках для калибровки
        self.last_left_hand_pose = left_hand_pose
        self.last_right_hand_pose = right_hand_pose
        
        self.process_arms_control(left_hand_pose, right_hand_pose)
    
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
            
        # Обработка команд для управления руками робота
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
        
        # Управление головой включено только при активном управлении руками
        if not self.head_control_enabled:
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
        # Добавляем базовые позиции для сброса
        target_pan = self.head_base_pan + np.clip(-y_rotation * self.head_sensitivity, -self.max_head_pan, self.max_head_pan)
        target_tilt = self.head_base_tilt + np.clip(-x_rotation * self.head_sensitivity, -self.max_head_tilt, self.max_head_tilt)
        
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
        
        # Обработка кнопок для управления руками и головой
        # Кнопка X (левая) - калибровка/начало управления
        if left_x > 0.5 and not self.button_states['left_x_pressed']:
            rospy.loginfo(f"Кнопка X нажата! Текущее состояние: {self.arm_control_state}")
            self.button_states['left_x_pressed'] = True
            if self.arm_control_state == 'idle':
                rospy.loginfo("Запуск калибровки...")
                self.start_arm_calibration()
            elif self.arm_control_state == 'calibrating':
                rospy.loginfo("Завершение калибровки...")
                self.finish_arm_calibration()
        elif left_x <= 0.5:
            self.button_states['left_x_pressed'] = False
        
        # Кнопка Y (левая) - остановка управления
        if left_y > 0.5 and not self.button_states['left_y_pressed']:
            self.button_states['left_y_pressed'] = True
            if self.arm_control_state == 'controlling':
                self.stop_arm_control()
        elif left_y <= 0.5:
            self.button_states['left_y_pressed'] = False
        
        # Управление захватом рук
        if self.arm_control_state == 'controlling':
            self.control_grippers(left_grip, right_grip, left_index, right_index)
    
    def process_arms_control(self, left_hand_pose, right_hand_pose):
        """
        Обработка управления руками робота на основе новой логики:
        - Y контроллера -> sho_pitch
        - Z контроллера -> sho_roll  
        - X контроллера -> el_yaw
        - Наклон X контроллера -> el_pitch
        """
        if self.arm_control_state != 'controlling':
            return
        
        if self.calibration_data['left_hand_base'] is None or self.calibration_data['right_hand_base'] is None:
            return
        
        # Вычисляем относительные смещения от калибровочных позиций
        left_offset = self.calculate_hand_offset(left_hand_pose, self.calibration_data['left_hand_base'])
        right_offset = self.calculate_hand_offset(right_hand_pose, self.calibration_data['right_hand_base'])
        
        # Получаем наклоны контроллеров
        left_tilt = self.get_controller_tilt(self.left_controller_orientation, self.calibration_data['left_controller_base'])
        right_tilt = self.get_controller_tilt(self.right_controller_orientation, self.calibration_data['right_controller_base'])
        
        # Логируем данные для отладки
        rospy.loginfo_throttle(1, 
            f"Новое управление - Левая: Y={left_offset['y']:.3f}->sho_pitch, Z={left_offset['z']:.3f}->sho_roll, "
            f"X={left_offset['x']:.3f}->el_yaw, наклон={left_tilt:.3f}->el_pitch | "
            f"Правая: Y={right_offset['y']:.3f}->sho_pitch, Z={right_offset['z']:.3f}->sho_roll, "
            f"X={right_offset['x']:.3f}->el_yaw, наклон={right_tilt:.3f}->el_pitch"
        )
        
        # Преобразуем в команды сервоприводов по новой логике
        self.convert_to_new_servo_commands(left_offset, right_offset, left_tilt, right_tilt)
    
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
    
    def start_arm_calibration(self):
        """
        Начинает калибровку рук. Оператор должен выставить руки в стартовую позу.
        """
        rospy.loginfo("=== НАЧАЛО КАЛИБРОВКИ РУК ===")
        rospy.loginfo(f"Текущее состояние: {self.arm_control_state}")
        
        self.arm_control_state = 'calibrating'
        self.head_control_enabled = False  # Отключаем управление головой во время калибровки
        
        # Сбрасываем голову в базовое положение
        self.reset_head_to_base()
        
        rospy.loginfo("=== КАЛИБРОВКА РУК ===")
        rospy.loginfo("Выставьте руки в стартовую позу и нажмите X для завершения калибровки")
        rospy.loginfo("Ожидание данных о руках...")
    
    def finish_arm_calibration(self):
        """
        Завершает калибровку и начинает управление руками.
        """
        rospy.loginfo("=== ЗАВЕРШЕНИЕ КАЛИБРОВКИ ===")
        rospy.loginfo(f"Текущее состояние: {self.arm_control_state}")
        
        # Сохраняем текущие позиции рук как базовые
        # Данные о руках должны быть получены в последнем pose_callback
        rospy.loginfo("Сохранение калибровочных данных...")
        
        # Проверяем, что у нас есть данные о руках и контроллерах
        if (hasattr(self, 'last_left_hand_pose') and hasattr(self, 'last_right_hand_pose') and
            self.left_controller_orientation is not None and self.right_controller_orientation is not None):
            rospy.loginfo("Данные о руках и контроллерах найдены, сохраняем калибровку...")
            self.calibration_data['left_hand_base'] = self.last_left_hand_pose
            self.calibration_data['right_hand_base'] = self.last_right_hand_pose
            self.calibration_data['left_controller_base'] = self.left_controller_orientation
            self.calibration_data['right_controller_base'] = self.right_controller_orientation
            self.calibration_data['head_base'] = self.operator_head_pose
            
            self.arm_control_state = 'controlling'
            self.head_control_enabled = True  # Включаем управление головой
            rospy.loginfo("=== КАЛИБРОВКА ЗАВЕРШЕНА ===")
            rospy.loginfo("Новая система управления руками активирована:")
            rospy.loginfo("  - Y контроллера -> sho_pitch")
            rospy.loginfo("  - Z контроллера -> sho_roll")
            rospy.loginfo("  - X контроллера -> el_yaw")
            rospy.loginfo("  - Наклон X контроллера -> el_pitch")
            rospy.loginfo("Нажмите Y для остановки")
        else:
            rospy.logwarn("Нет данных о руках или контроллерах для калибровки. Попробуйте еще раз.")
            rospy.logwarn("Убедитесь, что VR гарнитура подключена и передает данные")
            self.arm_control_state = 'idle'
    
    def stop_arm_control(self):
        """
        Останавливает управление руками и головой, возвращает их в стартовую позу.
        """
        self.arm_control_state = 'idle'
        self.head_control_enabled = False  # Отключаем управление головой
        rospy.loginfo("=== ОСТАНОВКА УПРАВЛЕНИЯ РУКАМИ И ГОЛОВОЙ ===")
        rospy.loginfo("Возврат рук в стартовую позу...")
        
        # Возвращаем руки в стартовую позу
        self.set_arms_to_start_position()
        
        # Сбрасываем захваты в закрытое положение
        self.reset_grippers()
        
        # Очищаем данные калибровки
        self.calibration_data = {
            'left_hand_base': None,
            'right_hand_base': None,
            'left_controller_base': None,
            'right_controller_base': None,
            'head_base': None
        }
        
        rospy.loginfo("Готово. Нажмите X для новой калибровки")
    
    def reset_head_to_base(self):
        """
        Сбрасывает голову в базовое положение.
        """
        rospy.loginfo("Сброс головы в базовое положение...")
        self.send_head_command(self.head_base_pan, self.head_base_tilt)
        self.current_head_pan = self.head_base_pan
        self.current_head_tilt = self.head_base_tilt
        rospy.loginfo(f"Голова сброшена: pan={self.head_base_pan:.2f}, tilt={self.head_base_tilt:.2f}")
    
    def reset_grippers(self):
        """
        Сбрасывает захваты в центральное положение (500).
        """
        rospy.loginfo("Сброс захватов в центральное положение...")
        
        # Сбрасываем состояния захватов в центральное положение
        self.left_gripper_state = 0.5
        self.right_gripper_state = 0.5
        
        # Отправляем команды в центральное положение (500)
        arm_msg = SetBusServosPosition()
        arm_msg.duration = 0.5
        
        positions = [
            # BusServoPosition(id=21, position=500),   # Левый захват (ОТКЛЮЧЕН)
            BusServoPosition(id=22, position=500)     # Правый захват в центре
        ]
        
        arm_msg.position = positions
        self.arms_pub.publish(arm_msg)
        rospy.loginfo("Захваты сброшены в центральное положение (500)")
    
    def calculate_hand_offset(self, current_pose, base_pose):
        """
        Вычисляет смещение руки относительно калибровочной позиции.
        
        Args:
            current_pose: текущее положение руки
            base_pose: калибровочное положение руки
            
        Returns:
            dict: смещения по осям x, y, z
        """
        if base_pose is None:
            return {'x': 0, 'y': 0, 'z': 0}
        
        offset = {
            'x': current_pose.position.x - base_pose.position.x,
            'y': current_pose.position.y - base_pose.position.y,
            'z': current_pose.position.z - base_pose.position.z
        }
        
        return offset
    
    def get_controller_tilt(self, current_orientation, base_orientation):
        """
        Вычисляет наклон контроллера по оси X относительно калибровочного положения.
        
        Args:
            current_orientation: текущая ориентация контроллера
            base_orientation: калибровочная ориентация контроллера
            
        Returns:
            float: наклон по оси X в радианах
        """
        if base_orientation is None or current_orientation is None:
            return 0.0
        
        # Преобразуем кватернионы в углы Эйлера
        current_euler = self.quaternion_to_euler(
            current_orientation.x, current_orientation.y, 
            current_orientation.z, current_orientation.w
        )
        base_euler = self.quaternion_to_euler(
            base_orientation.x, base_orientation.y,
            base_orientation.z, base_orientation.w
        )
        
        # Вычисляем разность наклона по оси X (pitch)
        tilt_difference = current_euler[0] - base_euler[0]  # pitch (наклон вперед-назад)
        
        return tilt_difference
    
    def convert_to_new_servo_commands(self, left_offset, right_offset, left_tilt, right_tilt):
        """
        Преобразует смещения и наклоны в команды сервоприводов по новой логике.
        
        Args:
            left_offset: смещение левой руки (x, y, z)
            right_offset: смещение правой руки (x, y, z)
            left_tilt: наклон левого контроллера
            right_tilt: наклон правого контроллера
        """
        # Левая рука: Y->sho_pitch, Z->sho_roll, X->el_yaw, наклон->el_pitch
        left_angles = {
            'sho_pitch': self.left_arm_calibration['sho_pitch_base'] + int(left_offset['y'] * self.arm_sensitivity['y_to_sho_pitch']),
            'sho_roll': self.left_arm_calibration['sho_roll_base'] + int(left_offset['z'] * self.arm_sensitivity['z_to_sho_roll']),
            'el_yaw': self.left_arm_calibration['el_yaw_base'] + int(left_offset['x'] * self.arm_sensitivity['x_to_el_yaw']),
            'el_pitch': self.left_arm_calibration['el_pitch_base'] + int(left_tilt * self.arm_sensitivity['tilt_x_to_el_pitch'])
        }
        
        # Правая рука: Y->sho_pitch, Z->sho_roll, X->el_yaw, наклон->el_pitch (зеркально)
        right_angles = {
            'sho_pitch': self.right_arm_calibration['sho_pitch_base'] - int(right_offset['y'] * self.arm_sensitivity['y_to_sho_pitch']),
            'sho_roll': self.right_arm_calibration['sho_roll_base'] - int(right_offset['z'] * self.arm_sensitivity['z_to_sho_roll']),
            'el_yaw': self.right_arm_calibration['el_yaw_base'] - int(right_offset['x'] * self.arm_sensitivity['x_to_el_yaw']),
            'el_pitch': self.right_arm_calibration['el_pitch_base'] - int(right_tilt * self.arm_sensitivity['tilt_x_to_el_pitch'])
        }
        
        # Ограничиваем углы пределами
        left_angles = self.limit_servo_angles(left_angles, 'left')
        right_angles = self.limit_servo_angles(right_angles, 'right')
        
        # Отправляем команды
        self.send_arm_commands(left_angles, right_angles)
    
    def limit_servo_angles(self, angles, hand_side):
        """
        Ограничивает углы сервоприводов специфичными пределами для каждой руки.
        
        Args:
            angles: словарь углов
            hand_side: 'left' или 'right'
            
        Returns:
            dict: ограниченные углы
        """
        limited_angles = {}
        
        for key, angle in angles.items():
            if key == 'sho_roll' and hand_side == 'left':
                # ID15 (l_sho_roll): максимум 800
                limited_angles[key] = int(max(100, min(800, angle)))
            elif key == 'sho_roll' and hand_side == 'right':
                # ID16 (r_sho_roll): минимум 200
                limited_angles[key] = int(max(200, min(900, angle)))
            else:
                # Остальные сервоприводы - стандартные ограничения
                limited_angles[key] = int(max(100, min(900, angle)))
        
        return limited_angles
    
    def convert_to_servo_commands(self, left_offset, right_offset):
        """
        Преобразует смещения рук в команды сервоприводов.
        
        Args:
            left_offset: смещение левой руки
            right_offset: смещение правой руки
        """
        # Простая обратная кинематика
        # Применяем масштабирование
        left_scaled = {
            'x': left_offset['x'] * self.scale_factor,
            'y': left_offset['y'] * self.scale_factor,
            'z': left_offset['z'] * self.scale_factor
        }
        
        right_scaled = {
            'x': right_offset['x'] * self.scale_factor,
            'y': right_offset['y'] * self.scale_factor,
            'z': right_offset['z'] * self.scale_factor
        }
        
        # Преобразуем в углы сервоприводов (упрощенная модель)
        left_angles = self.calculate_servo_angles(left_scaled, 'left')
        right_angles = self.calculate_servo_angles(right_scaled, 'right')
        
        # Отправляем команды
        self.send_arm_commands(left_angles, right_angles)
    
    def calculate_servo_angles(self, offset, hand_side):
        """
        Вычисляет углы сервоприводов на основе смещения руки.
        
        Args:
            offset: смещение руки (x, y, z) в метрах
            hand_side: 'left' или 'right'
            
        Returns:
            dict: углы для сервоприводов (0-1000)
        """
        # Улучшенная обратная кинематика
        # X -> поворот плеча вперед-назад (sho_pitch)
        # Y -> подъем плеча вверх-вниз (sho_roll)
        # Z -> поворот предплечья (el_yaw)
        
        # Коэффициенты для преобразования смещений в углы (радианы на метр)
        # 1 радиан ≈ 57.3 градуса, 1000 единиц = 2π радиан
        scale_x = 200 * self.arm_sensitivity['x']  # чувствительность X
        scale_y = 200 * self.arm_sensitivity['y']  # чувствительность Y  
        scale_z = 100 * self.arm_sensitivity['z']  # чувствительность Z
        
        # Отладочная информация
        rospy.loginfo_throttle(2, 
            f"Кинематика {hand_side}: offset={offset}, scale_x={scale_x}, scale_y={scale_y}, scale_z={scale_z}"
        )
        
        # Базовые позиции (стартовые позиции из конфигурации)
        if hand_side == 'left':
            base_sho_pitch = 874  # l_sho_pitch стартовая позиция
            base_sho_roll = 833   # l_sho_roll стартовая позиция
            base_el_pitch = 502   # l_el_pitch стартовая позиция
            base_el_yaw = 44      # l_el_yaw стартовая позиция
        else:
            base_sho_pitch = 126  # r_sho_pitch стартовая позиция
            base_sho_roll = 167   # r_sho_roll стартовая позиция
            base_el_pitch = 498   # r_el_pitch стартовая позиция
            base_el_yaw = 956     # r_el_yaw стартовая позиция
        
        angles = {}
        
        if hand_side == 'left':
            # Левая рука
            angles['sho_pitch'] = base_sho_pitch + int(offset['x'] * scale_x)  # l_sho_pitch
            angles['sho_roll'] = base_sho_roll + int(offset['y'] * scale_y)     # l_sho_roll
            angles['el_pitch'] = base_el_pitch  # l_el_pitch (пока не используем)
            angles['el_yaw'] = base_el_yaw + int(offset['z'] * scale_z)         # l_el_yaw
        else:
            # Правая рука (зеркальная)
            angles['sho_pitch'] = base_sho_pitch - int(offset['x'] * scale_x)  # r_sho_pitch
            angles['sho_roll'] = base_sho_roll - int(offset['y'] * scale_y)    # r_sho_roll
            angles['el_pitch'] = base_el_pitch  # r_el_pitch (пока не используем)
            angles['el_yaw'] = base_el_yaw - int(offset['z'] * scale_z)        # r_el_yaw
        
        # Ограничиваем углы специфичными пределами для каждого сервопривода
        # ID15 (l_sho_roll): максимум 800
        if 'sho_roll' in angles and hand_side == 'left':
            angles['sho_roll'] = int(max(100, min(800, angles['sho_roll'])))
        # ID16 (r_sho_roll): минимум 200
        elif 'sho_roll' in angles and hand_side == 'right':
            angles['sho_roll'] = int(max(200, min(900, angles['sho_roll'])))
        # Остальные сервоприводы - стандартные ограничения
        else:
            for key in angles:
                if key != 'sho_roll':  # sho_roll уже обработан выше
                    angles[key] = int(max(100, min(900, angles[key])))
        
        # Дополнительная проверка: убеждаемся, что все значения положительные целые числа
        for key in angles:
            angles[key] = int(max(0, angles[key]))
        
        return angles
    
    def send_arm_commands(self, left_angles, right_angles):
        """
        Отправляет команды управления руками.
        
        Args:
            left_angles: углы для левой руки
            right_angles: углы для правой руки
        """
        arm_msg = SetBusServosPosition()
        arm_msg.duration = 0.1  # Быстрое обновление
        
        positions = []
        
        # Левая рука (правильные ID из URDF)
        if left_angles:
            positions.append(BusServoPosition(id=13, position=int(max(0, left_angles['sho_pitch']))))   # l_sho_pitch
            positions.append(BusServoPosition(id=15, position=int(max(0, left_angles['sho_roll']))))    # l_sho_roll
            positions.append(BusServoPosition(id=17, position=int(max(0, left_angles['el_pitch']))))  # l_el_pitch
            positions.append(BusServoPosition(id=19, position=int(max(0, left_angles['el_yaw']))))     # l_el_yaw
        
        # Правая рука (правильные ID из URDF)
        if right_angles:
            positions.append(BusServoPosition(id=14, position=int(max(0, right_angles['sho_pitch']))))  # r_sho_pitch
            positions.append(BusServoPosition(id=16, position=int(max(0, right_angles['sho_roll']))))  # r_sho_roll
            positions.append(BusServoPosition(id=18, position=int(max(0, right_angles['el_pitch']))))  # r_el_pitch
            positions.append(BusServoPosition(id=20, position=int(max(0, right_angles['el_yaw']))))    # r_el_yaw
        
        arm_msg.position = positions
        self.arms_pub.publish(arm_msg)
        
        # Логируем команды для отладки
        rospy.loginfo_throttle(1, f"Команды рук - Левые: {left_angles}, Правые: {right_angles}")
    
    def control_grippers(self, left_grip, right_grip, left_index, right_index):
        """
        Управление захватами рук на основе значений grip и index контроллеров.
        
        Args:
            left_grip: значение grip левого контроллера (0.0-1.0)
            right_grip: значение grip правого контроллера (0.0-1.0)
            left_index: значение index левого контроллера (0.0-1.0)
            right_index: значение index правого контроллера (0.0-1.0)
        """
        if self.arm_control_state != 'controlling':
            return
        
        # Логика управления захватами:
        # index = 1.0 -> сжимает захват (уменьшает угол)
        # grip = 1.0 -> разжимает захват (увеличивает угол)
        # Если отпустить кнопки, захват остается в последнем положении
        
        # Левый захват (ВРЕМЕННО ОТКЛЮЧЕН - сервопривод сломан)
        # if left_index > 0.5:  # Сжимаем
        #     self.left_gripper_state = max(0.0, self.left_gripper_state - 0.1)
        # elif left_grip > 0.5:  # Разжимаем
        #     self.left_gripper_state = min(1.0, self.left_gripper_state + 0.1)
        
        # Правый захват
        if right_index > 0.5:  # Сжимаем
            self.right_gripper_state = max(0.0, self.right_gripper_state - 0.1)
        elif right_grip > 0.5:  # Разжимаем
            self.right_gripper_state = min(1.0, self.right_gripper_state + 0.1)
        
        # Преобразуем состояние в углы сервоприводов
        # Центральное положение = 500, пределы ±200
        # Левый захват инвертирован: 0.0 = открыт (700), 1.0 = закрыт (300)
        # Правый захват: 0.0 = закрыт (300), 1.0 = открыт (700)
        left_gripper_pos = int(500 + (1.0 - self.left_gripper_state) * 200)  # Инвертировано
        right_gripper_pos = int(500 + self.right_gripper_state * 200)  # Обычно
        
        # Ограничиваем углы пределами ±200 от центрального положения
        left_gripper_pos = max(300, min(700, left_gripper_pos))
        right_gripper_pos = max(300, min(700, right_gripper_pos))
        
        # Отправляем команды захватам (левый захват ВРЕМЕННО ОТКЛЮЧЕН)
        arm_msg = SetBusServosPosition()
        arm_msg.duration = 0.1
        
        positions = [
            # BusServoPosition(id=21, position=left_gripper_pos),   # Левый захват (ОТКЛЮЧЕН)
            BusServoPosition(id=22, position=right_gripper_pos)  # Правый захват
        ]
        
        arm_msg.position = positions
        self.arms_pub.publish(arm_msg)
    
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
