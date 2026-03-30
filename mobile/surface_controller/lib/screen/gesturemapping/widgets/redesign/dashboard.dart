import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class Dashboard extends StatelessWidget {
  const Dashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: getProportionalHeight(context, 166),
      width: getProportionalHeight(context, 155),
      decoration: BoxDecoration(
        color: const Color.fromARGB(255, 255, 255, 255),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color.fromARGB(100, 0, 0, 0),
            spreadRadius: 1,
            blurRadius: 5,
            offset: const Offset(2, 2), // changes position of shadow
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Image(
                  image: AssetImage("assets/redesign/AC_icon.png"),
                  width: 30,
                  height: 38,
                ),
                Image(
                  image: AssetImage("assets/redesign/more.png"),
                  width: 33,
                  height: 28,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "Philips",
              textAlign: TextAlign.left,
              style: TextStyle(fontWeight: FontWeight.w900),
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "Tv Turn on",
              textAlign: TextAlign.left,
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Row(
            children: [
              Image(
                image: AssetImage("assets/redesign/hand.png"),
                width: 50,
                height: 50,
              ),
              const SizedBox(width: 35),
              const Expanded(
                child: Text(
                  "Thumb and index",
                  softWrap: true,
                  maxLines: 2,
                  overflow: TextOverflow.visible,
                  textAlign: TextAlign.left,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
