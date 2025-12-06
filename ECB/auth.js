function isAuthenticated(req, res, next) {
  if (req.session.user) {
    return next();
  }
  res.redirect('/login');
}

function isAdmin(req, res, next) {
  if (req.session.user && req.session.user.isAdmin) {
    return next();
  }
  res.status(403).send('需要管理员权限');
}

module.exports = {
  isAuthenticated,
  isAdmin
};