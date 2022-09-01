// Instance the tour
var tour = new Tour({
  steps: [
  {
    path: "",
    element: "#recently-uploaded-text",
    title: "Title of my step",
    content: "Content of my step"
  },
  {
    path: "",
    element: "#new-user-box",
    title: "Title of my next step",
    content: "Content of my next step"
  },
  {
    path: "/problems",
    element: "#myTable",
    title: "testing the different page tour",
    content: "Content of my next step"
  },
  {
    path: "/credits",
    element: "#title",
    title: "why is this not working i am sad",
    content: "content"
  }],
  animation: true,
  smartPlacement: true
});