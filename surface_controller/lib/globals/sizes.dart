import 'package:flutter/material.dart';

// Function to get proportional sizes based on screen width
double getProportionalWidth(BuildContext context, double baseSize) {
  double screenWidth = MediaQuery.of(context).size.width;
  // Using 375 as base width (common mobile width)
  return (screenWidth / 375.0) * baseSize;
}

// Function to get proportional sizes based on screen height
double getProportionalHeight(BuildContext context, double baseSize) {
  double screenHeight = MediaQuery.of(context).size.height;
  // Using 812 as base height (common mobile height)
  return (screenHeight / 812.0) * baseSize;
}
