"""
Simple verification script for CacheManager
"""
import asyncio
from app.core.cache import CacheManager


class MockRedis:
    """Mock Redis client for testing"""
    def __init__(self):
        self.store = {}
        self.ttls = {}
    
    async def get(self, key: str):
        if key in self.store:
            return self.store[key].encode('utf-8')
        return None
    
    async def setex(self, key: str, ttl: int, value: str):
        self.store[key] = value
        self.ttls[key] = ttl
    
    async def delete(self, key: str):
        if key in self.store:
            del self.store[key]
        if key in self.ttls:
            del self.ttls[key]


async def test_cache_manager():
    """Test CacheManager functionality"""
    print("Testing CacheManager...")
    
    # Create mock Redis and CacheManager
    mock_redis = MockRedis()
    cache = CacheManager(mock_redis)
    
    # Test 1: generate_cache_key
    print("\n1. Testing generate_cache_key...")
    key1 = cache.generate_cache_key("train", from_station="BJP", to_station="SHH", date="2025-01-15")
    key2 = cache.generate_cache_key("train", date="2025-01-15", to_station="SHH", from_station="BJP")
    assert key1 == key2, "Keys should be consistent regardless of parameter order"
    print(f"   ✓ Generated key: {key1}")
    print(f"   ✓ Keys are consistent: {key1 == key2}")
    
    # Test 2: set and get
    print("\n2. Testing set and get...")
    test_key = "test:key"
    test_value = "test_value"
    await cache.set(test_key, test_value, ttl=300)
    retrieved = await cache.get(test_key)
    assert retrieved == test_value, f"Expected {test_value}, got {retrieved}"
    print(f"   ✓ Set value: {test_value}")
    print(f"   ✓ Retrieved value: {retrieved}")
    print(f"   ✓ TTL set to: {mock_redis.ttls.get(test_key)} seconds")
    
    # Test 3: delete
    print("\n3. Testing delete...")
    await cache.delete(test_key)
    retrieved = await cache.get(test_key)
    assert retrieved is None, "Value should be None after deletion"
    print(f"   ✓ Value deleted successfully")
    
    # Test 4: get non-existent key
    print("\n4. Testing get non-existent key...")
    result = await cache.get("non_existent_key")
    assert result is None, "Should return None for non-existent key"
    print(f"   ✓ Returns None for non-existent key")
    
    # Test 5: default TTL
    print("\n5. Testing default TTL (5 minutes = 300 seconds)...")
    await cache.set("ttl_test", "value")
    ttl = mock_redis.ttls.get("ttl_test")
    assert ttl == 300, f"Expected TTL 300, got {ttl}"
    print(f"   ✓ Default TTL is 300 seconds (5 minutes)")
    
    print("\n✅ All CacheManager tests passed!")


if __name__ == "__main__":
    asyncio.run(test_cache_manager())
