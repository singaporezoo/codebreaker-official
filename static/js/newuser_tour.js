// Instance the tour
var tour = new Tour({
  steps: [
  {
    path: "",
    element: "#recently-uploaded-text",
    title: "Title of my step",
    content: "Content of my step",
    placement: "top"
  },
  {
    path: "",
    element: "#new-user-box",
    title: "Title of my next step",
    content: "Content of my next step",
    placement: "left"
  },
  {
    path: "/problems",
    element: "#myTable",
    title: "testing the different page tour",
    content: "Content of my next step",
    placement: "bottom"
  }],
  backdrop: true
});
tour.init();
$("#start-tour-btn").click(function() {
  tour.restart();
});
