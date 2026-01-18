# Project Owner Checklist

**You are receiving ownership of this URW Mall Analytics project. This guide will help you set up the infrastructure so your team can collaborate effectively.**

---

## Overview

As the project owner, you need to:
1. Set up data versioning infrastructure (DVC remote)
2. Provide credentials to team members
3. Configure repository settings

---

## Step 1: Set Up Data Versioning (DVC Remote)

### Why You Need This
- Team members need to pull/push datasets without Git (files are too large)
- Ensures everyone works with the same data versions
- Tracks data lineage and pipeline reproducibility

### Choose Your Storage Backend

#### Option A: OVH Object Storage (Original Setup)

**Setup Steps:**
1. Create OVH Public Cloud account: https://www.ovhcloud.com/
2. Create Object Storage container:
   - Go to Public Cloud → Object Storage → Create container
   - Container name: `urw-data-challenge` (or your choice)
   - Region: Choose closest to your team
   - Container type: Private
3. Create S3 credentials:
   - Go to Public Cloud → Object Storage → S3 Users
   - Create a new S3 user
   - **SAVE THESE CREDENTIALS** (shown only once):
     - `Access Key` → This is your `OVH_ACCESS_KEY_ID`
     - `Secret Key` → This is your `OVH_SECRET_ACCESS_KEY`

4. Configure DVC remote in the project:
```bash
cd /path/to/urw-data-challenge

# Add OVH S3 remote
dvc remote add -d ovh-storage s3://urw-data-challenge
dvc remote modify ovh-storage endpointurl https://s3.gra.io.cloud.ovh.net
```

5. Configure your local credentials (do NOT commit):
```bash
# Add to .env
echo "OVH_ACCESS_KEY_ID=your_access_key_here" >> .env
echo "OVH_SECRET_ACCESS_KEY=your_secret_key_here" >> .env

# Configure DVC
source .env
dvc remote modify --local ovh-storage access_key_id $OVH_ACCESS_KEY_ID
dvc remote modify --local ovh-storage secret_access_key $OVH_SECRET_ACCESS_KEY
```

6. Push existing data to remote:
```bash
dvc push
```

7. **Share with team**: Give them the credentials (use secure method: 1Password, LastPass, encrypted message)

#### Option B: AWS S3

**Setup Steps:**
1. Create AWS account: https://aws.amazon.com/
2. Create S3 bucket:
   - S3 Console → Create bucket
   - Bucket name: `urw-data-challenge`
   - Region: Choose closest to your team
   - Block all public access: Yes
3. Create IAM user for DVC access:
   - IAM Console → Users → Add user
   - User name: `dvc-user`
   - Access type: Programmatic access
   - Permissions: Attach `AmazonS3FullAccess` (or custom bucket-only policy)
   - **SAVE CREDENTIALS**: Access key ID and Secret access key
4. Configure DVC remote:
```bash
dvc remote add -d s3remote s3://urw-data-challenge/dvc-storage
dvc remote modify s3remote region eu-west-1  # your region
```

#### Option C: Local Remote (Simplest, Single-Machine)

For single-user or local development:
```bash
dvc remote add -d localremote /path/to/storage/folder
```

#### Option D: Google Drive

For small teams without cloud infrastructure:
```bash
dvc remote add -d gdrive gdrive://folder_id_here
```

---

## Step 2: Share Credentials with Team

### What to Share

**For DVC (Data Versioning):**
- Storage backend type (OVH, S3, etc.)
- Bucket/container name
- Access credentials (access key + secret key)
- Endpoint URL (if OVH or other S3-compatible)

### Credentials Document Template

Create a document (store in password manager) with this info:

```
URW Mall Analytics - Team Credentials
=====================================

PROJECT REPOSITORY
URL: https://github.com/your-org/urw-data-challenge
Main Branch: main

DVC REMOTE STORAGE (OVH Object Storage)
Container: urw-data-challenge
Endpoint: https://s3.gra.io.cloud.ovh.net
Access Key ID: xxxxxxxxxxxxxxxxxxxxx
Secret Access Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

SETUP INSTRUCTIONS
See: docs/SETUP.md
Owner Checklist: docs/PROJECT_OWNER_CHECKLIST.md
```

---

## Step 3: Update Project Documentation

### Update .env.example

Update `.env.example` with your actual endpoint (DO NOT include secrets):

```bash
# .env.example
# DVC Remote Storage (OVH Object Storage)
OVH_ACCESS_KEY_ID=your_access_key_from_owner
OVH_SECRET_ACCESS_KEY=your_secret_key_from_owner
```

### Update DVC Configuration

If you changed DVC remote setup, update `.dvc/config`:

```bash
# Commit this to Git
git add .dvc/config
git commit -m "Update DVC remote configuration"
git push
```

---

## Step 4: Onboard Team Members

1. **Provide Access:**
   - GitHub repository: Add as collaborator
   - DVC credentials: Share via secure method

2. **Direct them to setup docs:**
   - [SETUP.md](SETUP.md) - Complete setup guide
   - [DVC_WORKFLOW.md](DVC_WORKFLOW.md) - Data versioning workflow

---

## Verification Checklist

Before inviting team members, verify:

### DVC Remote
- [ ] Bucket/storage created and accessible
- [ ] Credentials generated and saved securely
- [ ] Successfully ran `dvc push` from your machine
- [ ] Tested `dvc pull` on a fresh clone (or different directory)

### Documentation
- [ ] `.env.example` updated with correct endpoint info
- [ ] `docs/SETUP.md` reviewed and accurate
- [ ] `README.md` has correct quick start instructions
- [ ] Credentials document prepared (stored securely)

### Repository
- [ ] All code committed and pushed
- [ ] `.gitignore` includes `.env`, `.dvc/config.local`
- [ ] CI/CD pipeline passing (GitHub Actions)
- [ ] Repository permissions set correctly

### Team Access
- [ ] GitHub repository access granted
- [ ] Credentials shared securely
- [ ] Onboarding instructions sent

---

## Support Resources

### For You (Project Owner)
- DVC Documentation: https://dvc.org/doc
- OVH Object Storage Docs: https://docs.ovh.com/gb/en/storage/object-storage/
- AWS S3 Docs: https://docs.aws.amazon.com/s3/

### For Team Members
- `docs/SETUP.md` - Complete setup guide
- `docs/DVC_WORKFLOW.md` - Data versioning workflow
- `README.md` - Project overview and quick start

---

## You're Done!

Once you've completed this checklist:
1. Team can clone the repository
2. Team can `dvc pull` to get data
3. Team can run the pipeline (`dvc repro`)
4. Team can launch the dashboard
5. Team can collaborate on development

---

**Questions?** Create an issue in the repository or reach out to the original team members listed in README.md.
