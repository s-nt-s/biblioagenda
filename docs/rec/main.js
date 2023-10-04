function url_to_dom() {
    const zona = document.getElementById("zona");
    const tipo = document.getElementById("tipo");

    document.location.search.substring(1).split(/&/g).forEach(value=>{
        if (value.length==0) return;
        if (zona.querySelector("option[value='"+value+"']")) zona.value=value;
        if (tipo.querySelector("option[value='"+value+"']")) tipo.value=value;
    });
}

function dom_to_url() {
    const zona = document.getElementById("zona");
    const tipo = document.getElementById("tipo");

    const qr = [
        zona.value,
        tipo.value
    ].filter(v=>v.length>0).join("&");

    if (qr.length==0 && document.location.search.length==0) return;
    if (qr.length>0 && document.location.search=='?'+qr) return;
    const url = document.location.href.replace(/\?.*$/,"");
    if (qr.length==0) {
        console.log(document.location.href, "->", url);
        history.pushState({}, "", url);
        return;
    }
    console.log(document.location.href, "->", url+'?'+qr);
    history.pushState(qr, "", url+'?'+qr);
}

function filtrar() {
    const getVal = (id) => document.getElementById(id).value.trim();
    const setHide = (span, val) => {
        if (val.length==0) span.classList.remove("hide");
        else span.classList.add("hide");
    }
    const zona = getVal("zona");
    const tipo = getVal("tipo");
    const trs = document.querySelectorAll("table tbody tr");

    let count = 0;
    trs.forEach(tr=>{
        const z = tr.querySelector("span[data-zona]");
        const t = tr.querySelector("span[data-tipo]");
        //setHide(z, zona);
        //setHide(t, tipo);
        const hide = (() => {
            const izona = z.getAttribute("data-zona").split(/\s+/g);
            if (zona.length!=0 && !izona.includes(zona)) return true;
            if (tipo.length!=0 && tipo!=t.getAttribute("data-tipo")) return true;
            return false;
        })();
        if (hide) tr.classList.add("hide");
        else {
            count++;
            tr.classList.remove("hide");
            tr.classList.remove(count%2==0?"odd":"even");
            tr.classList.add(count%2==0?"even":"odd");
            
        }
    });
    dom_to_url();
}

document.addEventListener("DOMContentLoaded", function() {
    url_to_dom();
    zona.addEventListener("change", filtrar)
    tipo.addEventListener("change", filtrar)
    filtrar();
});