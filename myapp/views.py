from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpRequest
from django.contrib import messages
import hashlib
from .firebase import auth_instance,db   
import time, threading
from django.utils import timezone
import random
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .firebase import storage 
import uuid, math
import json
from django.views.decorators.csrf import csrf_exempt
import os, re
from uuid import uuid4 
from datetime import datetime, timedelta
import logging
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.views import View
from collections import Counter
# Create your views here.
def home(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Authenticate user with Firebase Authentication
            user = auth_instance.sign_in_with_email_and_password(email, password)
            user_id = user["localId"]

            # Fetch user data from Firebase
            user_data = db.child("users").child(user_id).get().val()

            if not user_data:
                messages.error(request, "User not found. Please log in again.")
                return redirect("home")

            # Generate OTP
            otp = random.randint(100000, 999999)

            # Update user session details in Firebase
            db.child("users").child(user_id).update({
                "otp": otp,
                "email": email,
                "timestamp": time.time()
            })

            # Save user_id in the session
            request.session["user_id"] = user_id

            # Send OTP via email
            subject = "Your OTP for Login"
            message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; background-color: #f9f9f9; padding: 20px;">
                    <h2 style="color: #4CAF50;">Your OTP for Login</h2>
                    <p style="font-size: 18px;">Please use the following OTP to complete your login:</p>
                    <div style="background-color: #e0f7fa; padding: 15px; border-radius: 5px; margin: 20px auto; width: fit-content;">
                        <strong style="font-size: 22px; color: #0277bd;">{otp}</strong>
                    </div>
                    <p style="color: #555;">This OTP is valid for 5 minutes.</p>
                </body>
            </html>
            """
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            try:
                send_mail(
                    subject,
                    "",
                    from_email,
                    recipient_list,
                    html_message=message
                )
                messages.success(request, "OTP has been sent to your email.")
                time.sleep(1.5)
                return redirect("OTPVerification")  # Redirect to OTP verification
            except Exception as e:
                messages.error(request, f"Failed to send OTP email: {e}")
                return redirect("home")
 
        except Exception as e:
            messages.error(request, f"Invalid credentials. Error: {e}")
            return redirect("home")

    return render(request, "index.html")




def OTPVerification(request):
    if request.method == "POST":
        input_otp = request.POST.get("otp")
        user_id = request.session.get("user_id")  # Fetch user_id from session

        if not user_id:
            messages.error(request, "User ID is missing. Please log in again.")
            return redirect("home")

        db.child("sessions").child(user_id).set({"user_id": user_id, "timestamp": time.time()})

        # Fetch session data from Firebase 
        session_data = db.child("sessions").child(user_id).get().val()
        if not session_data:
            messages.error(request, "Session expired. Please log in again.")
            return redirect("home")

        # Check OTP
        if str(input_otp) == str(session_data.get("otp")):
            # Remove OTP field
            updated_data = {k: v for k, v in session_data.items() if k != "otp"}
            db.child("users").child(user_id).set(updated_data)

            # Save user_id in the session
            request.session["user_id"] = user_id

            messages.success(request, "Logged in successfully.")
            #return redirect("userhomepage")  # Redirect to homepage
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("OTPVerification")

    # For GET request, fetch user_id from session
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "User ID is missing. Please log in again.")
        return redirect("home")

    return render(request, "verify-to-login.html", {"user_id": user_id})

