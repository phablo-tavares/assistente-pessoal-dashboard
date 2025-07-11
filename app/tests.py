from supabase_client import SupabaseClient


supabaseClient = SupabaseClient()
response = supabaseClient.getSpendingsByPhoneNumber('556299035665')
print(response)