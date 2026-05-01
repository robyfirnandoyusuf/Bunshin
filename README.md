# Kage Bunshin - 影分身の術
<img src="https://static.wikia.nocookie.net/naruto/images/7/75/Tumblr_m6a8ayWCtK1rput01o2_500.jpg/revision/latest?cb=20200322103745&path-prefix=vi" width="300px">

This tool is inspired by **Naruto's most iconic jutsu** the Shadow Clone Technique (影 = *Kage*, 分身 = *Bunshin*).

In the anime, Naruto creates **thousands of clones** that act simultaneously,
each one real and capable, overwhelming any target at the exact same moment. **Kage Bunshin** does the same thing, but for HTTP requests.

---

In security testing, a race condition only reveals itself when **hundreds or
thousands of requests hit an endpoint simultaneously** just like Naruto's clones overwhelming an enemy all at once.

One request? The server handles it fine.
**A thousand clones? The cracks start to show.**

---

## Usage

```py
from kage import Bunshin

tester = WebRaceTester(workers=30)

# Example 1: Test race condition pada endpoint redeem kupon
result = tester.race(
    url="https://localhost:8000/api/redeem-coupon",
    method="POST",
    headers={"Authorization": "Bearer TOKEN"},
    body={"coupon_code": "DISKON50"},
    count=25,
    test_name="double_redeem_coupon",
)
result.summary()

# Check suspecious response (unique from other requests)
for r in result.suspicious_responses():
    print(f"Thread {r.thread_id}: {r.status_code} => {r.body[:100]}")


# Example 2: Test race on transfer
result2 = tester.race(
    url="https://localhost:8000/api/transfer",
    method="POST",
    headers={
        "Authorization": "Bearer TOKEN",
        "Content-Type": "application/json",
    },
    body={"amount": 100, "to": "userY"},
    count=30,
    test_name="double_transfer",
)
result2.summary()
```
