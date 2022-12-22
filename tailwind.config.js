/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/*.{html,js,html.j2}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
