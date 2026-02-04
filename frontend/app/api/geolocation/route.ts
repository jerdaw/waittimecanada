import { NextResponse } from "next/server";

// Server-side IP geolocation to avoid CORS issues
export async function GET(request: Request) {
  try {
    // Get the client's IP from headers (works with most CDNs/proxies)
    const forwardedFor = request.headers.get("x-forwarded-for");
    const realIp = request.headers.get("x-real-ip");
    const clientIp = forwardedFor?.split(",")[0] || realIp || "";
    
    // Use ipapi.co for geolocation - server-side avoids CORS
    const ipToLookup = clientIp && clientIp !== "::1" && clientIp !== "127.0.0.1" 
      ? clientIp 
      : ""; // Empty string means use the requester's IP
    
    const apiUrl = ipToLookup 
      ? `https://ipapi.co/${ipToLookup}/json/`
      : "https://ipapi.co/json/";
    
    const response = await fetch(apiUrl, {
      headers: {
        "User-Agent": "WaitTimeCanada/1.0",
      },
    });
    
    if (!response.ok) {
      throw new Error(`IP geolocation failed: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.reason || "IP geolocation failed");
    }
    
    return NextResponse.json({
      success: true,
      location: {
        lat: data.latitude,
        lon: data.longitude,
        city: data.city,
        region: data.region,
        country: data.country_name,
      },
    });
  } catch (error) {
    console.error("IP geolocation error:", error);
    
    // Return a default location (Toronto) as fallback
    return NextResponse.json({
      success: true,
      location: {
        lat: 43.6532,
        lon: -79.3832,
        city: "Toronto",
        region: "Ontario",
        country: "Canada",
      },
      fallback: true,
    });
  }
}
