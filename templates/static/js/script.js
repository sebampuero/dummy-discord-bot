function objectifyForm(formArray) {//serialize data function

    var returnArray = {};
    for (var i = 0; i < formArray.length; i++) {
        returnArray[formArray[i]['name']] = formArray[i]['value'];
    }
    return returnArray;
}

function populateMembersSelect(membersArr) {
    let $members_select = $("#members_select")
    for(let i = 0; i < membersArr.length; i++){
        $members_select.append(`<option value="${membersArr[i]}">${membersArr[i]}</option>`)
    }
}

$(document).ready(function () {
    $(function () {

        $.ajax({
            type: "GET",
            url: "/bot/members",
            contentType: "application/json",
            success: function(data, textStatus, xhr) {
                let $form = $("form#send-form")
                let $cont = $("#no_members_container")
                membersArr = data.members
                if(membersArr.length == 0) {
                    $form.hide()
                    $cont.show()
                }else{
                    $cont.hide()
                    $form.show()
                    populateMembersSelect(membersArr)
                }
            }
        })


        var frm = $('#send-form');
        frm.submit(function (ev) {
            ev.preventDefault();
            obj = objectifyForm(frm.serializeArray())
            if (obj.text.length > 250) {
                alert("Texto muy grande")
                return;
            }
            $.ajax({
                type: frm.attr('method'),
                url: frm.attr('action'),
                data: JSON.stringify(obj),
                contentType: "application/json",
                success: function (data, textStatus, xhr) {
                    $("input#text").val("")
                    $("input#member_name").val("")
                    alert(data.message)
                }
            });
        });
    });
})