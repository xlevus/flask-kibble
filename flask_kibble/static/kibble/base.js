function RepeatedFormField(node){
    var $node = $(node);
    var tmpl = window.atob($node.data('template'))
    var delete_btn = $node.find('.delete-row');
    var add_btn = $node.find('.add-row');


    var row_count = function(){ 
        var len = $node.find('tr.formrow').length; 
        var empty = $node.find('tr.empty');

        if (len == 0) {
            empty.show();
            delete_btn.hide();
        } else {
            empty.hide();
            delete_btn.show();
        }
        return len;
    }


    add_btn.click(function(){
        var row = _.template(tmpl,
            {row_count: row_count()},
            {interpolate : /\{\{(.+?)\}\}/g});

        $(row).insertBefore($(this).parents('tr:first'));
        AutoWidget.refresh();
        row_count();
        return false;
    });

    delete_btn.click(function(){
        var toRem = $(this).parentsUntil('tr').parent().prev();
        toRem.remove();

        row_count();

        return false;
    });

    row_count();
}

$('.field-FieldList').each(function(i, elem){
    new RepeatedFormField($(elem).find('table'));
});
