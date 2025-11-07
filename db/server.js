const express = require('express');
const { connect } = require('./db/mongo');

const app = express();
app.use(express.json()); // for JSON bodies

connect();

// ... your routes here

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on ${PORT}`));

const postsRouter = require('./routes/posts');
app.use('/api/posts', postsRouter);

