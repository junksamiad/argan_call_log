import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")
table_name = os.getenv("AIRTABLE_TABLE_NAME", "call_log")

print(f"Testing Airtable connection...")
print(f"Base ID: {base_id}")
print(f"Table: {table_name}")

try:
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    print("✅ Table connection successful")
    
    # Try to get schema
    try:
        schema = table.schema()
        print(f"✅ Schema access successful")
        print(f"Schema type: {type(schema)}")
        print(f"Schema attributes: {dir(schema)}")
        
        # Check if it has fields attribute
        if hasattr(schema, 'fields'):
            print(f"✅ Schema has fields attribute")
            fields = schema.fields
            print(f"Fields type: {type(fields)}")
            print(f"Number of fields: {len(fields)}")
            
            for i, field in enumerate(fields[:3]):  # Show first 3 fields
                print(f"  Field {i}: {field}")
                print(f"  Field type: {type(field)}")
                if hasattr(field, 'name'):
                    print(f"  Field name: {field.name}")
                if hasattr(field, 'type'):
                    print(f"  Field type: {field.type}")
        else:
            print("❌ Schema has no fields attribute")
            
    except Exception as e:
        print(f"❌ Schema access failed: {e}")
        import traceback
        traceback.print_exc()
            
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc() 