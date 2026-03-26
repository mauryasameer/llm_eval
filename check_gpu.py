import mlx.core as mx

def check_metal():
    print("Checking MLX Metal GPU availability...")
    try:
        device = mx.default_device()
        print(f"Default MLX device: {device.type}")
        
        # Run a simple tensor operation
        a = mx.array([1.0, 2.0, 3.0])
        b = mx.array([4.0, 5.0, 6.0])
        c = a + b
        
        print(f"Test computation result: {c}")
        print("✅ Success: MLX is working correctly and your M2 GPU (Metal) is ready for inference.")
    except Exception as e:
        print(f"❌ Error during MLX operation: {e}")

if __name__ == "__main__":
    check_metal()
