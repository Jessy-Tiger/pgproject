# Pickup Request Email Flow Improvements

This document outlines the recent changes made to the project so that the pickup request form collects a sender email address, the admin notification is sent from that address with all form data included, and the user profile can hold/edit an email.

## Key Changes

1. **Model Updates**
   - Added `sender_email` field to `PickupRequest` model (`EmailField`, nullable).
   - Generated migration `0002_pickuprequest_sender_email.py` and applied it.

2. **Forms**
   - `PickupRequestForm` now includes `sender_email` (required).
   - `UserProfileForm` includes an email field to allow updating the user account email.

3. **Views**
   - `create_pickup_request` will save the sender email automatically and send notifications accordingly.
   - `complete_profile` pre-fills email and writes it back to `request.user.email` when the form is saved.

4. **Email Utility**
   - `send_email_notification` for `'new_request'` to admin uses the sender's email as the `from` address and sets a `Reply-To` header.
   - The email context and templates include the sender address and full payload details.

5. **Templates**
   - `customer/create_pickup.html` displays a new input control for sender email.
   - `emails/new_request_admin.html` shows sender email and all pickup data.
   - `profile/complete_profile.html` has an email field.
   - `shared/request_detail.html` now displays the correct sender email.

6. **Miscellaneous**
   - Adjusted profile viewing/editing flow to handle the email field.
   - Applied database migration.

## Testing Steps

1. Run the development server and create a new customer account or login as existing user.
2. Navigate to **Profile → Complete Profile** and verify you can see/edit the email field.
3. Go to **Create Pickup Request**; fill in the sender email along with other fields.
4. On submission, confirm a tracking number is assigned and no errors appear.
5. Check the admin email inbox (or console log) to ensure the message is:
   - Sent *from* the sender email.
   - Contains all entered information (sender address, receiver address, parcel details, etc.).
6. View the request detail page and confirm the sender email appears correctly.

## Notes

- If you're using the console backend for emails, the `from` field may still show the default host but the headers will contain the `Reply-To`.  You can inspect the raw output to verify.
- The new migration file must be checked into version control.

With these changes the mail flow should be smooth and error‑free as per the original requirements.