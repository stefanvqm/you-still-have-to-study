var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

const session = require('express-session');

var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var createNoteRouter = require('./routes/note');


var app = express();

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
  secret: 'your_secret_key', // Replace with an actual secret key
  resave: false,
  saveUninitialized: true,
  cookie: { secure: !true } // Set to true if using https
}));

// Middleware to make 'user' available to all templates
app.use(function(req, res, next) {
  if (req.session.message) {
    // Make the message accessible to the view
    res.locals.message = req.session.message;
    // Clear the message from the session
    delete req.session.message;
  }

  res.locals.username = req.session.username;

  next();
});

app.use('/', indexRouter);
app.use('/', usersRouter);
app.use('/', createNoteRouter);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
  // res.redirect('/')
});



module.exports = app;
