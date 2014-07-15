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

$('.jsupload').each(function(i, elem){
    var $elem = $(elem);
    var inpt = $elem.find('input[type=hidden]');
    var label = $elem.find('input[type=text]');
    
    var dz = new Dropzone(elem, {
        url: $elem.data('url'),
        previewsContainer: '.dropzone-upload-junk',
        paramName: inpt.attr('name'),
        clickable: $elem.find('.upload-button').get(0),
        init: function(){
            this.on('addedfile', function(){
                $elem.children('.upload-preview').removeClass('hidden');
            });
            this.on('uploadprogress', function(f, prog, bytes){
                $elem.find('[role=progressbar]').css('width', prog+'%')
            });
            this.on('success', function(f, resp){
                label.val(resp[inpt.attr('name')].filename);
                inpt.val(resp[inpt.attr('name')].blobkey);
                $elem.children('.upload-preview').addClass('hidden');
            });
        }
    });
});
