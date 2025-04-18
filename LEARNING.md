# Learnings

## Good things

- Made API stateless
- Learnt about SSR templates
- Was able to implememnt OTP based auth.
- Learnt about OpenAPI documentation
- Migrates to FastAPI (it was getting more difficult to work with plain json in flask and write documentatio)
- Learnt about python decorators, and using them as middlewares
- Learnt about `typing` in python
- Using json files to directly change states in server/android
- Learnt about GitLeaks
- Learnt about optimizing website, brought load time from 1min down to 13.55s in 3G conditions.

## Mistakes

### Using android platform

Since the application needs to avaliable to all students including the ones with iOS, we should have made a web app instead.

### Using a in-code debug flag

Should have used data inside a file as flag for debugging, or enviornment variable as debugging.

### Making such a bulk website

It looks good to one who already knows the app, but to a new student, he/she gets confused with so many iteractions possible.

### Using flask-only for production

Using flask for learning is well and good, but it doesn't come with many things needed out of the box. Which leads you to writing type unsafe code.