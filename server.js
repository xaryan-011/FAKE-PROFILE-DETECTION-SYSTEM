/**
 * ╔═══════════════════════════════════════════════════════════╗
 * ║      🛡️  Fake Profile Detection API  —  Node.js/Express  ║
 * ║      AI-powered system to detect fake social profiles     ║
 * ╚═══════════════════════════════════════════════════════════╝
 * 
 * Tech Stack: Node.js + Express + MySQL
 * Endpoints:  auth, predict, stats, history, extension, health
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');

// ── Import route modules ──
const authRoutes = require('./routes/auth');
const predictRoutes = require('./routes/predict');
const statsRoutes = require('./routes/stats');
const historyRoutes = require('./routes/history');

// ── Import DB init ──
const initDatabase = require('./models/db-init');

const app = express();
const PORT = process.env.PORT || 3000;

// ═══════════════════════════════════════
//  MIDDLEWARE
// ═══════════════════════════════════════

// CORS — allow frontend & Chrome extension
const allowedOrigins = (process.env.CORS_ORIGINS || '*').split(',').map((o) => o.trim());
app.use(
  cors({
    origin: allowedOrigins.includes('*') ? '*' : allowedOrigins,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);

// Parse JSON bodies
app.use(express.json({ limit: '10mb' }));

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    const status = res.statusCode;
    const color = status < 400 ? '\x1b[32m' : '\x1b[31m';
    console.log(
      `${color}${req.method}\x1b[0m ${req.originalUrl} → ${status} (${duration}ms)`
    );
  });
  next();
});

// ═══════════════════════════════════════
//  ROUTES
// ═══════════════════════════════════════

// Root
app.get('/', (req, res) => {
  res.json({
    message: '🛡️ Fake Profile Detection API',
    version: '1.0.0',
    stack: 'Node.js + Express + MySQL',
    docs: '/health',
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
  });
});

// Mount route modules
app.use('/', authRoutes);      // POST /register, POST /login
app.use('/', predictRoutes);   // POST /predict, POST /predict/batch, POST /api/extension/predict
app.use('/', statsRoutes);     // GET /stats
app.use('/', historyRoutes);   // GET /history

// ── Serve frontend static files (production) ──
const FRONTEND_BUILD = path.join(__dirname, '..', 'frontend', 'dist');
const fs = require('fs');
if (fs.existsSync(FRONTEND_BUILD)) {
  app.use('/assets', express.static(path.join(FRONTEND_BUILD, 'assets')));

  app.get('*', (req, res) => {
    const filePath = path.join(FRONTEND_BUILD, req.path);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      return res.sendFile(filePath);
    }
    res.sendFile(path.join(FRONTEND_BUILD, 'index.html'));
  });
}

// ═══════════════════════════════════════
//  ERROR HANDLING
// ═══════════════════════════════════════

// 404 handler
app.use((req, res) => {
  res.status(404).json({ detail: `Route ${req.method} ${req.originalUrl} not found` });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('❌ Unhandled error:', err.message);
  console.error(err.stack);
  res.status(500).json({ detail: 'Internal server error' });
});

// ═══════════════════════════════════════
//  STARTUP
// ═══════════════════════════════════════

async function start() {
  try {
    console.log('');
    console.log('🚀 Starting Fake Profile Detection API...');
    console.log('───────────────────────────────────────────');

    // Initialize database (create DB + tables)
    await initDatabase();

    // Start server
    app.listen(PORT, () => {
      console.log('───────────────────────────────────────────');
      console.log(`✅ Server running on http://localhost:${PORT}`);
      console.log(`📊 Health check: http://localhost:${PORT}/health`);
      console.log(`🔑 Auth:         POST /register, POST /login`);
      console.log(`🔍 Predict:      POST /predict`);
      console.log(`📈 Stats:        GET /stats`);
      console.log(`📋 History:      GET /history`);
      console.log('───────────────────────────────────────────');
      console.log('');
    });
  } catch (err) {
    console.error('❌ Failed to start server:', err.message);
    console.error('');
    console.error('💡 Make sure MySQL is running and the credentials in .env are correct.');
    console.error('   DB_HOST=' + (process.env.DB_HOST || 'localhost'));
    console.error('   DB_PORT=' + (process.env.DB_PORT || '3306'));
    console.error('   DB_USER=' + (process.env.DB_USER || 'root'));
    console.error('   DB_NAME=' + (process.env.DB_NAME || 'fake_profile_detection'));
    console.error('');
    process.exit(1);
  }
}

start();
