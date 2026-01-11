# Email Configuration Guide

This guide explains how to configure transactional emails for Splitwiser using Brevo (formerly Sendinblue).

## Why Brevo?

Brevo is recommended over Gmail because it:
- ✅ Provides better email deliverability
- ✅ Offers detailed analytics and tracking
- ✅ Has a generous free tier (300 emails/day)
- ✅ Is designed for transactional emails
- ✅ No "App Password" configuration needed

## Step 1: Create Brevo Account

1. Go to [Brevo](https://www.brevo.com/) and sign up
2. Verify your account via email

## Step 2: Add a Verified Sender

**Important:** Brevo requires a verified sender email address (not the SMTP login).

1. Go to **Senders & IP** → **Senders**
2. Click **Add a sender**
3. Enter your email address (e.g., `noreply@yourdomain.com` or personal email)
4. Verify the email address by clicking the link sent to that inbox

**Note:** You can use a free Gmail/personal email for testing, or your own domain for production.

## Step 3: Get SMTP Credentials

1. Go to **SMTP & API** in Brevo dashboard
2. Find your SMTP credentials:
   - **SMTP Server:** `smtp-relay.brevo.com`
   - **Port:** `587`
   - **Login:** Something like `9fc28f001@smtp-brevo.com`
3. Create an SMTP key:
   - Click **Generate a new SMTP key**
   - Give it a name (e.g., "Splitwiser Production")
   - Copy the key (you won't see it again!)

## Step 4: Configure Environment Variables

### For Local Development

Create a `.env` file in the `backend/` directory:

```bash
# Brevo SMTP Configuration
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_EMAIL=9fc28f001@smtp-brevo.com
SMTP_PASSWORD=<your-brevo-smtp-key>
FROM_EMAIL=noreply@yourdomain.com  # Your verified sender email
FROM_NAME=Splitwiser
FRONTEND_URL=http://localhost:5173
```

**Important:** Replace:
- `SMTP_EMAIL` with your Brevo SMTP login
- `SMTP_PASSWORD` with your Brevo SMTP key
- `FROM_EMAIL` with your verified sender email

### For Production (Fly.io)

Set secrets on Fly.io:

```bash
fly secrets set SMTP_HOST=smtp-relay.brevo.com
fly secrets set SMTP_PORT=587
fly secrets set SMTP_EMAIL=9fc28f001@smtp-brevo.com
fly secrets set SMTP_PASSWORD=<your-brevo-smtp-key>
fly secrets set FROM_EMAIL=noreply@yourdomain.com
fly secrets set FROM_NAME=Splitwiser
fly secrets set FRONTEND_URL=https://splitwiser.fly.dev
```

## Step 5: Test Email Configuration

Run the test script to verify your configuration:

```bash
cd backend
python test_email_config.py
```

This will:
1. Display your current email configuration
2. Check if all required variables are set
3. Send a test email to verify everything works

## Troubleshooting

### Error: "Sender not valid"

This means the `FROM_EMAIL` is not verified in Brevo.

**Solution:**
1. Go to Brevo → **Senders & IP** → **Senders**
2. Add and verify your sender email address
3. Update `FROM_EMAIL` environment variable to match

### Error: "Authentication failed"

This means your SMTP credentials are incorrect.

**Solution:**
1. Go to Brevo → **SMTP & API**
2. Generate a new SMTP key
3. Update `SMTP_PASSWORD` with the new key

### Error: "Email service not configured"

This means one or more required environment variables are missing.

**Solution:**
1. Run `python test_email_config.py` to see what's missing
2. Set all required variables (see Step 4 above)

### Emails not arriving

**Possible causes:**
1. Check spam folder
2. Verify sender email in Brevo
3. Check Brevo dashboard for delivery logs
4. Ensure you haven't exceeded free tier limits (300 emails/day)

## Email Templates

Splitwiser sends 4 types of transactional emails:

1. **Password Reset** - When user requests password reset
2. **Password Changed** - Confirmation after password change
3. **Email Verification** - When user changes email address
4. **Email Change Notification** - Security alert sent to old email

All templates include:
- Professional HTML design
- Plain text fallback
- Clear call-to-action buttons
- Security information

## Alternative Email Services

If you prefer not to use Brevo, these services also work:

### Gmail (Not Recommended for Production)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=<app-password>  # Not your regular password!
FROM_EMAIL=your-email@gmail.com
```

**Note:** Requires [App Password](https://support.google.com/accounts/answer/185833) setup.

### SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_EMAIL=apikey
SMTP_PASSWORD=<your-sendgrid-api-key>
FROM_EMAIL=noreply@yourdomain.com
```

### AWS SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_EMAIL=<your-iam-username>
SMTP_PASSWORD=<your-iam-password>
FROM_EMAIL=noreply@yourdomain.com
```

## Security Best Practices

1. **Never commit credentials** - Use environment variables or secrets management
2. **Use verified sender domains** - Improves deliverability and trust
3. **Monitor email logs** - Check Brevo dashboard regularly
4. **Rotate SMTP keys** - Periodically generate new keys for security
5. **Use custom domain** - Better than personal email for production

## Support

For issues:
- Brevo Support: https://help.brevo.com/
- Splitwiser Issues: https://github.com/vincewoo/splitwiser/issues
