<?php
$token = $argv[1];
$domain = $argv[2];
$courseid = $argv[3];
$assignmentid = $argv[4];
$grades = json_decode($argv[5], true);

$functionname = 'mod_assign_save_grades';
$params = array('assignmentid' => '1',
                'applytoall' => '1',
                'grades' => $grades);

header('Content-Type: text/plain');
$serverurl = $domain . '/webservice/rest/server.php'. '?wstoken=' . $token . '&wsfunction='.$functionname;

require_once('php/curl.php');

$curl = new curl;
$restformat = '&moodlewsrestformat=json';
$resp = $curl->post($serverurl . $restformat, $params);
print_r($resp);
