function poll_dashboard() {
    $("#dashboard").load("/data");
}

poll_dashboard();
setInterval(poll_dashboard, 1000 * 300);  // 5 Minutes
