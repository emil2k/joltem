// -------------------------------------------------------------------
// Markdown Joltem Set
// -------------------------------------------------------------------
mySettings = {
	onShiftEnter:		{keepDefault:false, openWith:'\n\n'},
	markupSet: [
        // {name:'First Level Heading', key:'1', placeHolder:'Your title here...', closeWith:function(markItUp) { return miu.markdownextraTitle(markItUp, '=') }, className: 'miuHeader1' },
        // {name:'Second Level Heading', key:'2', placeHolder:'Your title here...', closeWith:function(markItUp) { return miu.markdownextraTitle(markItUp, '-') }, className: 'miuHeader2' },
        // {name:'Heading 3', key:'3', openWith:'### ', placeHolder:'Your title here...', className: 'miuHeader3' },
        // {name:'Heading 4', key:'4', openWith:'#### ', placeHolder:'Your title here...', className: 'miuHeader4' },
        // {name:'Heading 5', key:'5', openWith:'##### ', placeHolder:'Your title here...', className: 'miuHeader5' },
        // {name:'Heading 6', key:'6', openWith:'###### ', placeHolder:'Your title here...', className: 'miuHeader6' },
		// {separator:'---------------' },
		{name:'Bold', key:'B', openWith:'**', closeWith:'**', className: 'miuBold'},
		{name:'Italic', key:'I', openWith:'_', closeWith:'_', className: 'miuItalic'},
		{separator:'---------------' },
		{name:'Bulleted List', openWith:'- ', className: 'miuBulletedList' },
		{name:'Numeric List', openWith:function(miu) { return miu.line+'. '; }, className: 'miuNumericList'},
		{separator:'---------------' },
		{name:'Picture', key:'P', replaceWith:'![[![Alternative text]!]]([![Url:!:http://]!] "[![Title]!]")', className: 'miuPicture'},
		{name:'Link', key:'L', openWith:'[', closeWith:']([![Url:!:http://]!] "[![Title]!]")', placeHolder:'Your text to link here...', className: 'miuLink' },
		{name:'Definition', key:'D', openWith:'Term\n', placeHolder:':    Your definition here ', className: 'miuDefinition' },
		{separator:'---------------'},
		{name:'Quotes', openWith:'> ', className: 'miuQuotes'},
		{
            name:'Code Block / Code',
            key: 'K',
            openWith:'~~~~.[![Language]!]\n',
            closeWith:'\n~~~~',
            placeHolder:'Your code here...',
            className: 'miuCode'
        },
		{separator:'---------------'},
		// {name:'Table',
			// header:" header ",
			// seperator:" ------ ",
			// placeholder:" data   ",
            // className: 'miuTable',
			// replaceWith:function(h) {
				// cols = prompt("How many cols?");
				// rows = prompt("How many rows?");
				// out = "";
				// // header row
				// for (c = 0; c < cols; c++) {
						// out += "|"+(h.header||"");
				// }
				// out += "|\n";
				// // seperator
				// for (c = 0; c < cols; c++) {
						// out += "|"+(h.seperator||"");
				// }
				// out += "|\n";
				// for (r = 0; r < rows; r++) {
					// for (c = 0; c < cols; c++) {
						// out += "|"+(h.placeholder||"");
					// }
					// out += "|\n";
				// }
				// return out;
			// }
		// },
		{name:'Preview', call:'preview', className:"preview"}
	]
}

// mIu nameSpace to avoid conflict.
miu = {
	markdownextraTitle: function(markItUp, achar) {
		heading = '';
		n = $.trim(markItUp.selection||markItUp.placeHolder).length;
		for(i = 0; i < n; i++) {
			heading += achar;
		}
		return '\n'+heading;
	}
}
