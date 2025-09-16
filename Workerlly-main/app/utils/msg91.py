import requests

MSG91_TEMPLATE_ID = "672f510bd6fc0535714875e2"
MSG91_AUTH_KEY = "434154AnDd9jZr672f55b1P1"


async def send_otp(
    mobile: str,
    otp: str = "",
    otp_expiry: str = "10",
    param1: str = "",
    param2: str = "",
    param3: str = "",
) -> bool:
    url = f"https://control.msg91.com/api/v5/otp?template_id={MSG91_TEMPLATE_ID}&mobile={mobile}&authkey={MSG91_AUTH_KEY}&otp={otp}&otp_expiry={otp_expiry}"
    payload = {"Param1": param1, "Param2": param2, "Param3": param3}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, verify=False)
    print(response.text)  # For debugging purposes
    return response.status_code == 200 and '"type":"success"' in response.text


async def verify_otp(mobile: str, otp: str) -> bool:
    url = f"https://control.msg91.com/api/v5/otp/verify?mobile={mobile}&otp={otp}&authkey={MSG91_AUTH_KEY}"
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        verify=False,
    )
    print(response.text)  # For debugging purposes
    return response.status_code == 200 and '"type":"success"' in response.text
