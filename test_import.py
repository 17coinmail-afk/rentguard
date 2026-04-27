import sys
sys.path.insert(0, r'C:\Users\ASUS\RentGuard')
try:
    import app
    print("OK")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("ERROR:", e)
