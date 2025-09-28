#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import JointState

class ButtonTest:
    def __init__(self):
        rospy.init_node('button_test', anonymous=True)
        
        # Состояния управления руками
        self.arm_control_state = 'idle'
        
        # Отслеживание нажатий кнопок
        self.button_states = {
            'left_x_pressed': False,
            'left_y_pressed': False
        }
        
        # Подписчик на данные VR контроллеров
        rospy.Subscriber('/quest/joints', JointState, self.joints_callback, queue_size=10)
        
        rospy.loginfo("Тест кнопок запущен. Нажмите X для калибровки")
    
    def joints_callback(self, joint_state):
        """
        Обработка данных о кнопках VR контроллеров.
        """
        if joint_state.name and joint_state.position:
            joint_dict = dict(zip(joint_state.name, joint_state.position))
            
            # Извлекаем данные о кнопках
            left_x = joint_dict.get('L_X', 0.0)
            left_y = joint_dict.get('L_Y', 0.0)
            
            # Логируем состояние кнопок
            rospy.loginfo_throttle(1, 
                f"Кнопки - X={left_x:.2f}, Y={left_y:.2f} | "
                f"Состояние: {self.arm_control_state} | "
                f"X нажата: {self.button_states['left_x_pressed']}"
            )
            
            # Обработка кнопки X
            if left_x > 0.5 and not self.button_states['left_x_pressed']:
                rospy.loginfo(f"=== КНОПКА X НАЖАТА! ===")
                rospy.loginfo(f"Текущее состояние: {self.arm_control_state}")
                self.button_states['left_x_pressed'] = True
                
                if self.arm_control_state == 'idle':
                    rospy.loginfo("Запуск калибровки...")
                    self.start_calibration()
                elif self.arm_control_state == 'calibrating':
                    rospy.loginfo("Завершение калибровки...")
                    self.finish_calibration()
            elif left_x <= 0.5:
                self.button_states['left_x_pressed'] = False
            
            # Обработка кнопки Y
            if left_y > 0.5 and not self.button_states['left_y_pressed']:
                rospy.loginfo(f"=== КНОПКА Y НАЖАТА! ===")
                self.button_states['left_y_pressed'] = True
                if self.arm_control_state == 'controlling':
                    self.stop_control()
            elif left_y <= 0.5:
                self.button_states['left_y_pressed'] = False
    
    def start_calibration(self):
        """Начинает калибровку"""
        self.arm_control_state = 'calibrating'
        rospy.loginfo("=== КАЛИБРОВКА НАЧАТА ===")
        rospy.loginfo("Нажмите X еще раз для завершения")
    
    def finish_calibration(self):
        """Завершает калибровку"""
        self.arm_control_state = 'controlling'
        rospy.loginfo("=== КАЛИБРОВКА ЗАВЕРШЕНА ===")
        rospy.loginfo("Управление активировано. Нажмите Y для остановки")
    
    def stop_control(self):
        """Останавливает управление"""
        self.arm_control_state = 'idle'
        rospy.loginfo("=== УПРАВЛЕНИЕ ОСТАНОВЛЕНО ===")
        rospy.loginfo("Нажмите X для новой калибровки")
    
    def run(self):
        """Основной цикл"""
        rospy.spin()

if __name__ == '__main__':
    try:
        test = ButtonTest()
        test.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Тест остановлен")
