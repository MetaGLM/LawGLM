
import fs from 'fs-extra';
import yaml from 'yaml';

if(!fs.pathExistsSync('config.yml'))
    throw new Error('config.yml not found');

export default yaml.parse(fs.readFileSync('config.yml').toString()) || {};