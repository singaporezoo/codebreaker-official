// Instance the tour
var tour = new Tour({
  steps: [
  {
    path: "/?tour=true",
    element: "#recently-uploaded-text",
    title: "Title of my step",
    content: "Content of my step",
    placement: "top"
  },
  {
    path: "/?tour=true",
    element: "#new-user-box",
    title: "Title of my next step",
    content: "Content of my next step",
    placement: "left"
  },
  {
    path: "/problems",
    element: "#problemlist-table-head",
    title: "testing the different page tour",
    content: "Content of my next step",
    placement: "top"
  }],
  backdrop: true,
  storage: window.localStorage,
  debug: true,
  framework: "bootstrap4",
  onEnd: function(tour){
    document.location.href="/";
  }
});

