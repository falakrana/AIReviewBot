function fetchData(url) {
    return fetch(url).then(res => res.json());
}

const processUser = (user) => {
    console.log(user.name);
}

class UserProxy {
    constructor(user) {
        this.user = user;
    }
    
    getName() {
        return this.user.name;
    }
}
