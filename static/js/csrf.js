(function(){
    function _getCookie(name){
        let v=null;
        if(document.cookie&&document.cookie!==''){
            const cs=document.cookie.split(';');
            for(let i=0;i<cs.length;i++){
                const c=cs[i].trim();
                if(c.substring(0,name.length+1)===(name+'=')){
                    v=decodeURIComponent(c.substring(name.length+1));
                    break;
                }
            }
        }
        return v;
    }
    if(!window.getCookie){ window.getCookie=_getCookie; }
})();
