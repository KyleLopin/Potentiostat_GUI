__author__ = 'Kyle Vitautas Lopin'

operation_params = {'low_cv_voltage': -500,  # units: mv
                    'high_cv_voltage': 500,  # units: mv
                    'sweep_rate': 1.0,  # units: V/s
                    'TIA_resistor': 20,  # units: k ohms
                    'PIDAC_resistor': 9.8,  # kilo ohms
                    'ADC_gain': 1,  # unitless
                    'number_IN_ENDPOINTS': 1,  # how many IN ENDPOINTS to connect to
                    'number_OUT_ENDPOINTS': 1,  # how many IN ENDPOINTS to connect to
                    'smallest_increment_pidac': 1./8.,  # the smallest increment the PIDAC is increased by
                    'clk_freq_isr_pwm': 24000000,  # frequency of the clock that is driving the PWM that triggers isrs
                    'virtual_ground_shift': 1024,  # mv shift in
                    'bits_PIDAC': 11,  # number of bits of the PIDAC
                    'adc_channel': 0,  # which adc channel to get
                    'PWM_period': 30000,  # value in the timing PWM period register
                    'PWM_compare': 15000,  # value in the timing PWM period register
                    'should_process': False}  # variable if the program should export the raw adc numbers or convert it

user_params = {'user_sets_label_after_run': False}  # let the user set the data label and make a note about data run