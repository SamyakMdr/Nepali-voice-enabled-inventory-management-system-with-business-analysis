import { useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  Text,
  View,
  Alert
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Make sure you have this image in your assets folder, or use a placeholder URI
const DummyProfile = require("../../assets/images/Dummy.png");

export default function Profile() {
  const router = useRouter();
  const [name, setName] = useState("Loading...");

  // 1. Load the user's name when the screen opens
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const storedName = await AsyncStorage.getItem("user_name");
        if (storedName) {
          setName(storedName);
        } else {
          setName("User"); // Fallback if no name found
        }
      } catch (error) {
        console.error("Failed to load profile", error);
      }
    };

    loadProfile();
  }, []);

  // 2. Handle Logout
  const handleLogout = async () => {
    try {
      // Clear all stored data (Token, Name, ID)
      await AsyncStorage.clear();
      
      Alert.alert("Logged Out", "See you soon!");
      
      // Redirect to Login Screen and reset history so they can't go back
      router.replace("/(auth)/login");
    } catch (error) {
      Alert.alert("Error", "Could not log out.");
    }
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-[#fff] mt-14 p-4"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View>
        <Text className="text-2xl font-bold mb-4 text-black dark:text-white">PROFILE</Text>
      </View>

      <View className="flex-col items-center justify-center mt-10 gap-4">
        {/* Profile Image */}
        <Image
          source={DummyProfile}
          style={{ width: 160, height: 160, borderRadius: 80 }} // Made slightly rounder
          resizeMode="cover"
        />
        
        {/* Dynamic Name */}
        <Text className="text-2xl my-10 font-semibold text-zinc-800 dark:text-zinc-200">
          {name}
        </Text>
      </View>

      <View>
        <Pressable onPress={handleLogout}>
          <Text className="text-center bg-[#FEE2E2] text-[#B91C1C] font-bold text-lg py-4 rounded-xl mt-10 overflow-hidden active:opacity-90">
            Logout
          </Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}