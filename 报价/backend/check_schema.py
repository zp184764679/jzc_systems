from api.schemas import ProcessBase, ProcessResponse

print("ProcessBase fields:")
for name, field in ProcessBase.model_fields.items():
    print(f"  {name}: {field.annotation}")

print("\nProcessResponse fields:")
for name, field in ProcessResponse.model_fields.items():
    print(f"  {name}: {field.annotation}")

print("\ndaily_fee in ProcessBase:", 'daily_fee' in ProcessBase.model_fields)
print("icon in ProcessBase:", 'icon' in ProcessBase.model_fields)
