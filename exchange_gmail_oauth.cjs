#!/usr/bin/env node
/**
 * Gmail OAuth Code Exchange Script
 * Part of Claude Autonomy Platform (ClAP)
 * 
 * Usage: node exchange_gmail_oauth.js "authorization_code_from_callback_url"
 * 
 * This script exchanges an OAuth authorization code for access/refresh tokens
 * when the Gmail MCP authentication flow times out or needs manual completion.
 * 
 * Required: Authorization code from OAuth callback URL
 * Example callback: http://localhost:3000/oauth2callback?code=4/0AVMBsJg...
 * 
 * Automatically saves credentials to ~/.gmail-mcp/credentials.json
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// OAuth configuration - reads from existing OAuth keys file
const OAUTH_KEYS_PATH = path.join(process.env.HOME, '.gmail-mcp', 'gcp-oauth.keys.json');

function loadOAuthConfig() {
    try {
        const oauthKeys = JSON.parse(fs.readFileSync(OAUTH_KEYS_PATH, 'utf8'));
        return {
            CLIENT_ID: oauthKeys.web.client_id,
            CLIENT_SECRET: oauthKeys.web.client_secret,
            REDIRECT_URI: oauthKeys.web.redirect_uris[0]
        };
    } catch (error) {
        console.error('Error loading OAuth configuration:', error);
        console.error('Expected file:', OAUTH_KEYS_PATH);
        process.exit(1);
    }
}

function exchangeCodeForTokens(authorizationCode, config) {
    const postData = new URLSearchParams({
        code: authorizationCode,
        client_id: config.CLIENT_ID,
        client_secret: config.CLIENT_SECRET,
        redirect_uri: config.REDIRECT_URI,
        grant_type: 'authorization_code'
    }).toString();

    const options = {
        hostname: 'oauth2.googleapis.com',
        path: '/token',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const tokens = JSON.parse(data);
                    resolve(tokens);
                } catch (error) {
                    reject(new Error(`Failed to parse token response: ${error.message}`));
                }
            });
        });

        req.on('error', (error) => {
            reject(error);
        });

        req.write(postData);
        req.end();
    });
}

function saveCredentials(tokens) {
    const credentialsPath = path.join(process.env.HOME, '.gmail-mcp', 'credentials.json');
    const credentials = {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        scope: tokens.scope,
        token_type: tokens.token_type,
        expiry_date: Date.now() + (tokens.expires_in * 1000)
    };
    
    // Ensure directory exists
    const dir = path.dirname(credentialsPath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(credentialsPath, JSON.stringify(credentials, null, 2));
    console.log('✅ Credentials saved to:', credentialsPath);
    
    // Calculate expiry time
    const expiryDate = new Date(credentials.expiry_date);
    console.log('🕒 Token expires at:', expiryDate.toLocaleString());
    
    return credentialsPath;
}

async function main() {
    // Check command line arguments
    if (process.argv.length < 3) {
        console.error('Usage: node exchange_gmail_oauth.js "authorization_code"');
        console.error('');
        console.error('Extract the authorization code from the OAuth callback URL:');
        console.error('http://localhost:3000/oauth2callback?code=YOUR_CODE_HERE');
        process.exit(1);
    }

    const authorizationCode = process.argv[2];
    
    console.log('🔄 Loading OAuth configuration...');
    const config = loadOAuthConfig();
    
    console.log('🔄 Exchanging authorization code for tokens...');
    
    try {
        const tokens = await exchangeCodeForTokens(authorizationCode, config);
        
        if (tokens.error) {
            console.error('❌ OAuth error:', tokens.error);
            console.error('Description:', tokens.error_description);
            process.exit(1);
        }
        
        if (!tokens.access_token) {
            console.error('❌ No access token received');
            console.error('Response:', tokens);
            process.exit(1);
        }
        
        console.log('✅ Token exchange successful!');
        saveCredentials(tokens);
        
        console.log('');
        console.log('🎉 Gmail MCP authentication complete!');
        console.log('💡 Next steps:');
        console.log('   1. Restart Claude Code session for MCP to pick up new credentials');
        console.log('   2. Test with: mcp__gmail__list_email_labels');
        
    } catch (error) {
        console.error('❌ Authentication failed:', error.message);
        process.exit(1);
    }
}

main();