package com.example.surface_controller

import android.content.Context
import android.net.wifi.WifiManager
import io.flutter.embedding.android.FlutterActivity
import android.os.Bundle

class MainActivity: FlutterActivity() {
    private var multicastLock: WifiManager.MulticastLock? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 1. Get the WifiManager
        val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        
        // 2. Create a lock that listens for ALL multicast packets
        multicastLock = wifiManager.createMulticastLock("senseeMulticastLock")
        multicastLock?.setReferenceCounted(true)
        
        // 3. Acquire it (This stops the OS from filtering the Pi's packets)
        multicastLock?.acquire()
    }

    override fun onDestroy() {
        super.onDestroy()
        multicastLock?.release()
    }
}