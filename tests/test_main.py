#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🚀 Test main execution block...")

if __name__ == "__main__":
    print("✅ Main block is executing")
    
    try:
        import sanctions
        print("✅ Sanctions module imported")
        
        print("🔍 Testing MF function...")
        df_mf = sanctions.get_mf_sanctions()
        print("✅ MF function completed")
        print("📊 MF records:", len(df_mf))
        
        print("🔍 Testing EU function...")
        df_eu = sanctions.get_eu_sanctions()
        print("✅ EU function completed")
        print("📊 EU records:", len(df_eu))
        
        print("🏁 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("🏁 Script finished")
