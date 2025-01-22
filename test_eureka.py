try:
    from py_eureka_client.eureka_client import EurekaClient
    print("EurekaClient imported successfully.")
except ImportError as e:
    print("ImportError:", e)
