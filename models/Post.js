// models/blog.js
const { Schema, model } = require('mongoose');

const PostSchema = new Schema({
  title: { type: String, required: true },
  content: { type: String, required: true },
  author: { type: String, default: 'Anonymous' },
  created_at: { type: Date, default: Date.now },
  // add any other fields you had in SQLite (e.g., tags, imageUrl)
}, { versionKey: false });

module.exports = model('Post', PostSchema);
