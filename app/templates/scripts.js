$('.add').on('click', add);
$('.remove').on('click', remove);

function add() {
  var new_line_no = parseInt($('#total_line').val()) + 1;
  var new_input =
"  <tr>
"                            <td><input
"                                type='month'
"                                id='start_date_xp_' " + new_line_no + "
"                                name='start_date_xp_' " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='month'
"                                id='stop_date_xp_' " + new_line_no + "
"                                name='stop_date_xp_' + " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='text'
"                                id='employer_' " + new_line_no + "
"                                name='employer_'' + " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='text'
"                                id='job_title_' " + new_line_no + "
"                                name='job_title_'' + " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='text'
"                                id='reference_' " + new_line_no + "
"                                name='reference_'' + " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='text'
"                                id='country_xp_' " + new_line_no + "
"                                name='country_xp_'' + " + new_line_no + "
"                                />
"                            </td>
"                            <td><input
"                                type='text'
"                                id='summary_xp_' " + new_line_no + "
"                                name='summary_xp_'' + " + new_line_no + "
"                                />
"                            </td>
"                        </tr>
"
;

  $('#experience').append(new_input);

  $('#total_line').val(new_line_no);
}

function remove() {
  var last_line_no = $('#total_line').val();

  if (last_line_no > 1) {
    $('#new_' + last_line_no).remove();
    $('#total_line').val(last_line_no - 1);
  }
}