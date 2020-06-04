import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)


class ADS1230TimingViolatedExcception(Exception):
    pass


class ADS1230(object):
    def __init__(self, pin_sclk, pin_dout):
        self.pin_sclk = pin_sclk
        self.pin_dout = pin_dout

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_sclk, GPIO.OUT)
        GPIO.setup(pin_dout, GPIO.IN)
        GPIO.output(pin_sclk, 0)

    def __del__(self):
        GPIO.cleanup()

    def calibrate(self):
        # calibration is done by pulsing 26 times

        for i in range(22):  # ignore first 22 values
            self._pulse_clk()

        for i in range(4):  # then pulse 4 times
            self._pulse_clk()
            if not GPIO.input(self.pin_dout) == 1:  # and check that DOUT is high
                logger.error("Data should be 1 during last 4 pulses for offset calibration.")
                return False

        return True  # is_ready can be used to check if calibration is done

    def is_ready(self):
        result = 0 == GPIO.input(self.pin_dout)
        logger.debug("data ready: {result}".format(result=result))
        return result

    def measure(self):
        tries = 0
        while not self.is_ready():
            if tries > 170:
                return False
            tries += 1
            time.sleep(0.05)

        result = 0

        for i in range(20):
            self._pulse_clk()
            current_bit = GPIO.input(self.pin_dout)
            result = (result << 1) | current_bit

        if result & 0x80000:  # signing bit
            result = -((result ^ 0xFFFFF) + 1)

        logger.debug("measured value {hex}, decimal {dec}".format(dec=result, hex=hex(result)))
        return result

    def _pulse_clk(self):
        before_pulse = time.perf_counter_ns()
        GPIO.output(self.pin_sclk, True)
        GPIO.output(self.pin_sclk, False)
        after_pulse = time.perf_counter_ns()

        high_time = after_pulse - before_pulse
        if high_time < 100:
            logger.error("SCKL was high for {high}ns which is less then the required pulse width of 100ns".format(
                high=high_time))
            raise ADS1230TimingViolatedExcception()
        elif high_time > 20000:
            logger.error("SCKL pulse width exceeded 20µs. Standby was enabled. Elapsed time: {elapsed}".format(
                elapsed=high_time))
            raise ADS1230TimingViolatedExcception()


class Loadcell:

    def __init__(self, pin_sclk, pin_dout):
        self.ads1230 = ADS1230(pin_sclk, pin_dout)
        self.ads1230.calibrate()
        self.zero_value = 0
        self.unit_value = 0

    def calibrate_zero(self):
        self.zero_value = self.ads1230.measure()

    def calibrate_unit(self, fraction=1.0):
        self.unit_value = (self.ads1230.measure() - self.zero_value) * (1.0 / fraction)

    def measure(self):
        return (self.ads1230.measure() - self.zero_value) / self.unit_value
