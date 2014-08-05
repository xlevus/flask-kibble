var gulp = require("gulp");

var paths = {
    css: ['frontend/app/*.css'],
    js: ['frontend/app/*.js'],
    dest: 'flask_kibble/static'
}

gulp.task("libs", function(){
    var mainBowerFiles = require("main-bower-files");
    var gulpFilter = require('gulp-filter');
    var minifycss = require('gulp-minify-css');
    var flatten = require('gulp-flatten');
    var rename = require('gulp-rename');
    var uglify = require('gulp-uglify');
    var concat = require('gulp-concat');
    var sourcemaps = require("gulp-sourcemaps");

    var jsFilter = gulpFilter("*.js");
    var cssFilter = gulpFilter("*.css");
    var fontFilter = gulpFilter(['*.eot', '*.woff', '*.svg', '*.ttf']);

    return gulp.src(mainBowerFiles())
        .pipe(jsFilter)
            .pipe(sourcemaps.init())
                .pipe(concat('libs.js'))
                .pipe(uglify({preserveComments: 'some'}))
                .pipe(rename({suffix: '.min'}))
            .pipe(sourcemaps.write('.'))
            .pipe(gulp.dest(paths.dest + '/js'))
            .pipe(jsFilter.restore())
        .pipe(cssFilter)
            .pipe(sourcemaps.init())
                .pipe(concat('libs.css')) 
            .pipe(sourcemaps.write('.'))
            .pipe(gulp.dest(paths.dest + '/css'))
            .pipe(cssFilter.restore())
        .pipe(fontFilter)
            .pipe(flatten())
            .pipe(gulp.dest(paths.dest + '/fonts'));
});

gulp.task('css', function(){
    var concat = require('gulp-concat');

    return gulp.src(paths.css)
        .pipe(concat('kibble.css'))
        .pipe(gulp.dest(paths.dest + '/css'));
});

gulp.task('js', function(){
    var concat = require('gulp-concat');

    return gulp.src(paths.js)
        .pipe(concat('kibble.js'))
        .pipe(gulp.dest(paths.dest + '/js'));
});

gulp.task('clean', function(){
    var del = require('del');
    del(paths.dest, function() {});
});

gulp.task("default", ['libs', 'css', 'js']);

