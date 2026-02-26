import time
import random
from src.detector import DetectionEngine


def random_ip():
    return f"192.168.{random.randint(0,255)}.{random.randint(0,255)}"


def scenario_advanced_test():

    print("Starting advanced scenario simulation...")

    engine = DetectionEngine(clock=time.time)

    slow_attack_ip = random_ip()

    print("Simulating slow attack pattern...")

    for _ in range(15):
        engine.process_failed_login(slow_attack_ip)
        time.sleep(0.2)

    burst_ip = random_ip()

    print("Simulating burst attack pattern...")

    for _ in range(6):
        engine.process_failed_login(burst_ip)


    print("Simulating random IP event flood...")

    for _ in range(30):
        engine.process_failed_login(random_ip())
        if random.random() < 0.3:
            time.sleep(0.05)

    print("Advanced scenario test completed.")


if __name__ == "__main__":
    scenario_advanced_test()